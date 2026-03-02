# SPDX-License-Identifier: BSD-2-Clause
""" Provides the basic support to build a package. """

# Copyright (C) 2021 EDISOFT
# Copyright (C) 2020, 2026 embedded brains GmbH & Co. KG
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from contextlib import contextmanager
import copy
import fnmatch
import graphlib
import itertools
import os
import logging
import subprocess
from typing import Any, Callable, Iterable, Iterator, Optional, Type, Union

from specitems import (augment_glossary_terms, data_digest, EnabledSet,
                       is_enabled, Item, ItemCache, ItemDataByUID,
                       ItemGetValueContext, ItemGetValue, ItemMapper,
                       ItemSelection, ItemView, Link, link_is_enabled,
                       pickle_load_data_by_uid, SphinxContent, SphinxMapper,
                       to_iterable)
from specware import SpecWareTypeProvider, run_command


class BuildItemTypeProvider(SpecWareTypeProvider):
    """ Provides a type system for specification build items. """

    def __init__(self, data_by_uid: ItemDataByUID) -> None:
        data_by_uid.update(
            pickle_load_data_by_uid(
                os.path.join(os.path.dirname(__file__), "spec.pickle")))
        super().__init__(data_by_uid)
        dict_info = self.data_by_uid["/spec/root"]["spec-info"]["dict"]
        dict_info["mandatory-attributes"] = list(
            sorted(dict_info["attributes"].keys()))
        dict_info["attributes"]["workspace-hash"] = {
            "description": None,
            "spec-type": "sha256"
        }


def _git_has_staged_files(directory: str) -> bool:
    stdout: list[str] = []
    status = run_command(["git", "diff", "--name-only", "--cached"], directory,
                         stdout)
    assert status == 0
    return bool(stdout)


def _get_input_links(item: Item) -> Iterator[Link]:
    yield from itertools.chain(item.links_to_parents("input"),
                               item.links_to_children("input-to"))


def build_item_input(item: Item, name: str) -> Item:
    """ Return the first input item with the name.  """
    for link in _get_input_links(item):
        if link["name"] == name:
            return link.item
    raise KeyError


def _get_spec(ctx: ItemGetValueContext) -> Any:
    return ctx.item.spec


def _basename(value: str) -> str:
    return os.path.basename(value)


def _dash(value: str) -> str:
    return f"-{value}" if value else ""


def _dirname(value: str) -> str:
    return os.path.dirname(value)


def _relpath(value: str, start: str) -> str:
    return os.path.relpath(value, start)


def _slash(value: str) -> str:
    return f"/{value}" if value else ""


class BuildItemMapper(SphinxMapper):
    """
    The build item mapper provides a method to get a link to the primary
    documentation place of the item.
    """

    def __init__(self, item: Item):
        super().__init__(item)
        self.add_default_get_value("spec", _get_spec)
        self.add_value_transformer("basename", _basename)
        self.add_value_transformer("dirname", _dirname)
        self.add_value_transformer("dash", _dash)
        self.add_value_transformer("relpath", _relpath)
        self.add_value_transformer("slash", _slash)

    def get_link(self, item: Item, document_key: None | str = None) -> str:
        """
        Return a link to the item.

        The document key selects the preferred target document.  If it is not
        available for item, then the default document will be the link target.
        """
        raise NotImplementedError


def _get_input_or_output(ctx: ItemGetValueContext,
                         what: Callable[[str], "BuildItem"]) -> Any:
    name_end = ctx.remaining_path.find("/")
    build_item = what(ctx.remaining_path[:name_end])
    return ctx.reset(build_item.item, ctx.remaining_path[name_end + 1:])


class BuildItem():
    """ Represents a package build item. """

    # pylint: disable=too-many-public-methods
    @classmethod
    def prepare_factory(cls, _factory: "BuildItemFactory",
                        _type_name: str) -> None:
        """ Prepare the build item factory for the type. """

    def __init__(self,
                 director: "PackageBuildDirector",
                 item: Item,
                 mapper: Optional[BuildItemMapper] = None) -> None:
        self.director = director
        self.item = item
        if mapper is None:
            mapper = BuildItemMapper(item)
        self.mapper = mapper
        try:
            component = self.input("component")
            assert isinstance(component, PackageComponent)
        except KeyError:
            component = None
        self._component_stack = [component]
        mapper.add_default_get_value("component", self._get_component)
        director.factory.add_get_values_to_mapper(self.mapper)
        my_type = self.item.type
        self.mapper.add_get_value(f"{my_type}:/input", self._get_input)
        self.mapper.add_get_value(f"{my_type}:/output", self._get_output)
        self.description = SphinxContent()
        self.description.add(item.get("build-description", None))

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, BuildItem):
            return NotImplemented
        return self.item == other.item  # pylint: disable=protected-access

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, BuildItem):
            return NotImplemented
        return self.item < other.item  # pylint: disable=protected-access

    def __hash__(self) -> int:
        return hash(self.item)

    def __contains__(self, key: str) -> bool:
        return key in self.item

    def __getitem__(self, key: str) -> Any:
        return self.substitute(self.item[key])

    def __setitem__(self, key: str, value: Any) -> None:
        self.item[key] = value

    def get(self, key: str, default: Any) -> Any:
        """
        Get the substitution of the attribute value if the attribute exists,
        otherwise the substitution of the default value is returned.
        """
        return self.substitute(self.item.get(key, default))

    @property
    def uid(self) -> str:
        """ Is the UID of the build item. """
        return self.item.uid

    @property
    def enabled_set(self) -> EnabledSet:
        """ Is the enabled set of the build item. """
        return self.item.cache.enabled_set

    @property
    def enabled(self) -> bool:
        """ Is true, if the build item is enabled, otherwise false.  """
        return self.item.enabled

    @property
    def component(self) -> "PackageComponent":
        """ Is the package component of the build item. """
        the_component = self._component_stack[-1]
        if the_component is None:
            raise StopIteration
        return the_component

    @component.setter
    def component(self, the_component: "PackageComponent") -> None:
        """ Set the package component of the build item. """
        self._component_stack[-1] = the_component

    @property
    def component_depth(self) -> int:
        """ Is the package component stack depth of the build item. """
        return len(self._component_stack)

    @property
    def git_directory(self) -> str:
        """ Is the package Git directory. """
        return self.director.package["deployment-directory"]

    def push_component(self, component: "PackageComponent") -> None:
        """
        Push the component to the top of the package component stack.
        """
        self._component_stack.append(component)

    def pop_component(self) -> None:
        """ Pop the top from the package component stack. """
        self._component_stack.pop()

    @contextmanager
    def component_scope(self, component: "PackageComponent") -> Iterator[None]:
        """ Opens a package component context. """
        self.push_component(component)
        item_cache = self.item.cache
        item_cache.push_selection(component.selection)
        item_cache.push_view(component.view)
        yield
        item_cache.pop_view()
        item_cache.pop_selection()
        self.pop_component()

    def do_run(self) -> None:
        """ Run the build. """
        self.mapper.item = self.item
        self.discard_outputs()
        self.clear_description()
        logging.info("%s: run", self.uid)
        self.run()
        self.refresh_outputs()
        self.refresh_make_and_input_links()
        self.refresh()
        self.commit("Refresh")
        assert not self.director.use_git or self.git_is_clean()

    def build(self, **kwargs) -> None:
        """ Run the build if necessary. """
        self.mapper.item = self.item
        logging.info("%s: check if build is necessary", self.uid)
        necessary = self.is_build_necessary()
        if necessary:
            logging.info("%s: build is necessary", self.uid)
        force: bool = kwargs.get("force", False)
        if force:
            logging.info("%s: build is forced", self.uid)
        if force or necessary:
            self.do_run()
        else:
            logging.info("%s: build is unnecessary", self.uid)

    def label(self, item: Optional[Item] = None) -> str:
        """ Get the label of the build item description. """
        if item is None:
            item = self.item
        return f"PackageItem{item.ident}"

    def reference(self) -> str:
        """ Get a reference to the build item description. """
        return self.description.get_reference(self.label(), self.item.spec)

    def clear_description(self) -> None:
        """ Clear the build item description. """
        self.description = SphinxContent()

    def _store_description(self) -> None:
        description = "\n".join(self.description)
        key = "build-description"
        if description:
            self.item[key] = description
        else:
            self.item.data.pop(key, None)

    def add_build_section(self, **kwargs) -> None:
        """ Add the build section to the content. """
        content: SphinxContent = kwargs["content"]
        with content.section(self.item.spec, label=self.label()):
            inputs = [item.reference() for item in sorted(set(self.inputs()))]
            if len(inputs) == 1:
                content.add(f"Use input {inputs[0]}.")
            else:
                content.add_list(inputs, prologue="Use the following inputs:")
            description: str | SphinxContent = self.description
            if not description:
                description = "Support the package build."
            content.add(description)

    def has_changed(self, link: Link) -> bool:
        """
        Return true, if the build item state changed with respect to the state
        of the link, otherwise false.
        """
        return link["hash"] is None or self.digest() != link["hash"]

    def needs_build(self) -> bool:
        """
        Return true, if the build item needs a build, otherwise returns false.
        """
        return False

    def is_build_necessary(self) -> bool:
        """ Return true, if the build is necessary, otherwise false. """
        necessary = False
        for link in itertools.chain(
                self.item.links_to_parents(("make", "input"),
                                           is_link_enabled=link_is_enabled),
                self.item.links_to_children("input-to",
                                            is_link_enabled=link_is_enabled)):
            if not link.item.enabled:
                logging.info("%s: input is disabled: %s", self.uid,
                             link.item.uid)
                continue
            build_item = self.director[link.item.uid]
            if link["hash"] is None:
                logging.info("%s: input is new: %s", self.uid, build_item.uid)
            if build_item.has_changed(link):
                logging.info("%s: input has changed: %s", self.uid,
                             build_item.uid)
                necessary = True
            else:
                logging.info("%s: input has not changed: %s", self.uid,
                             build_item.uid)
        for link in self.item.links_to_parents(
                "output", is_link_enabled=link_is_enabled):
            if not link.item.enabled:
                logging.info("%s: output is disabled: %s", self.uid,
                             link.item.uid)
                continue
            build_item = self.director[link.item.uid]
            if build_item.needs_build():
                logging.info("%s: output needs build: %s", self.uid,
                             build_item.uid)
                necessary = True
            else:
                logging.info("%s: output build is not mandatory: %s", self.uid,
                             build_item.uid)
        return necessary

    def is_present(self) -> bool:
        """
        Return true, if the build item state is present, otherwise false.
        """
        return True

    def discard(self) -> None:
        """ Discard the data associated with the build item.  """

    def discard_outputs(self) -> None:
        """ Discard all outputs of the build item.  """
        logging.info("%s: discard outputs", self.uid)
        for item in self.item.parents("output",
                                      is_link_enabled=link_is_enabled):
            if not item.enabled:
                logging.info("%s: output is disabled: %s", self.uid, item.uid)
                continue
            item["build-description"] = None
            build_item = self.director[item.uid]
            build_item.discard()
            build_item.clear_description()

    def clear(self) -> None:
        """ Clear the state of the build item.  """

    def lazy_verify(self) -> bool:
        """ Lazily verify the state of the build item.  """
        return True

    def refresh(self) -> None:
        """ Refresh the build item state.  """

    def commit(self, reason: str) -> None:
        """ Commit the build item state.  """
        logging.info("%s: commit: %s", self.uid, reason)
        files = [self.item.file]
        for item in self.item.children("input-to"):
            item.save()
            files.append(item.file)
        self._store_description()
        self.item.save()
        self.git_add(files)
        self.git_commit(reason)

    def digest(self) -> str:
        """ Return the digest of the build item. """
        data = copy.deepcopy(self.item.data)
        for link in data["links"]:
            if link["role"] == "input-to":
                link["hash"] = None
        for link in self.item.links_to_children("input-to"):
            data["links"].append(link.data)
        data.pop("workspace-hash", None)
        return data_digest(data)

    def refresh_link(self, link: Link) -> None:
        """ Refresh the link to reflect the state of the build item. """
        link["hash"] = self.digest()

    def refresh_outputs(self) -> None:
        """ Refresh all outputs of the build item.  """
        logging.info("%s: refresh outputs", self.uid)
        for item in self.item.parents("output"):
            uid = item.uid
            build_item = self.director[uid]
            build_item.refresh_make_and_input_links()
            build_item.refresh()
            build_item.commit("Refresh output")

    def refresh_make_and_input_links(self) -> None:
        """ Refresh all make and input links of the build item.  """
        logging.info("%s: refresh make and input links", self.uid)
        for link in itertools.chain(self.item.links_to_parents("make"),
                                    _get_input_links(self.item)):
            self.director[link.item.uid].refresh_link(link)

    def _make(self, parent_links: Iterator[Link], child_links: Iterator[Link],
              make_link: Link) -> None:
        """ Make the outputs using the linked item.  """
        # Create a temporary item using duplicated data to make sure the maker
        # item uses no persistent state
        item_cache = self.item.cache
        item = Item(item_cache, make_link.item.uid,
                    copy.deepcopy(make_link.item.data))
        item["make-params"] = make_link["params"]
        item.init_parents(item_cache)
        # The maker item has no links to children by itself
        for link in parent_links:
            item.add_link_to_parent(link)
        for link in child_links:
            item.add_link_to_child(link)
        item.add_link_to_parent(
            Link(
                self.item, {
                    "name": make_link["output-name"],
                    "role": "output",
                    "uid": self.item.uid
                }))
        item_cache.type_provider.set_type(item)
        director = self.director
        maker = director.factory.create(director, item)
        maker.run()
        self.description.add(maker.description)

    def run(self) -> None:
        """ Run the build item tasks. """
        item = self.item
        for make_link in item.links_to_parents("make"):
            self._make(item.links_to_parents(("input", "output")),
                       item.links_to_children("input-to"), make_link)

    def substitute(self, data: Any, item: Optional[Item] = None) -> Any:
        """
        Recursively substitute the data using the item mapper of the build
        step.
        """
        if item is None:
            item = self.item
        return self.mapper.substitute_data(data, item)

    def input(self, name: str) -> "BuildItem":
        """ Return the first input associated with the name. """
        for link in _get_input_links(self.item):
            if link["name"] == name:
                return self.director[link.item.uid]
        raise KeyError

    def inputs(self, name: Optional[str] = None) -> Iterator["BuildItem"]:
        """ Yield the inputs associated with the name. """
        for link in _get_input_links(self.item):
            if name is None or link["name"] == name:
                yield self.director[link.item.uid]

    def input_link(self,
                   name: Optional[str] = None) -> tuple[Link, "BuildItem"]:
        """ Return the first link and input pair associated with the name. """
        for link in _get_input_links(self.item):
            if link["name"] == name:
                return link, self.director[link.item.uid]
        raise KeyError

    def input_links(
            self,
            name: Optional[str] = None) -> Iterator[tuple[Link, "BuildItem"]]:
        """ Yield the link and input pairs associated with the name. """
        for link in _get_input_links(self.item):
            if name is None or link["name"] == name:
                yield link, self.director[link.item.uid]

    def input_link_by_key(self, name: str, key: str,
                          value: str) -> tuple[Link, "BuildItem"]:
        """
        Get the input associated with the name and a key with the value.
        """
        for link in _get_input_links(self.item):
            if name is None or link["name"] == name and link[key] == value:
                return link, self.director[link.item.uid]
        raise ValueError(f"{self.uid}: has no {name} input with attribute "
                         f"{key} equal to {value}")

    def output(self, name: str) -> "BuildItem":
        """
        Return the first directory state production associated with the
        name.
        """
        for link in self.item.links_to_parents(
                "output", is_link_enabled=link_is_enabled):
            if link["name"] == name:
                if link.item.enabled:
                    return self.director[link.item.uid]
                logging.info("%s: output is disabled: %s", self.uid,
                             link.item.uid)
                raise KeyError
        raise KeyError

    def git_add(self, what: Union[str, Iterable[str]]) -> None:
        """ Add the files to Git. """
        if not self.director.use_git:
            return
        directory = self.git_directory
        what = to_iterable(what)
        submodules = self.director.submodules
        if submodules:
            what = [path for path in what if not path.startswith(submodules)]
        what = [os.path.relpath(path, directory) for path in what]
        if what:
            command = [
                "git", "add", "--force", "--pathspec-from-file=-",
                "--pathspec-file-nul"
            ]
            logging.info(
                "%s: add files %s to Git by running in '%s' "
                "with file list provided by stdin: %s", self.uid, what,
                directory, " ".join(command))
            subprocess.run(command,
                           check=True,
                           input="\0".join(what).encode("utf-8"),
                           cwd=directory)

    def git_is_clean(self) -> bool:
        """
        Return true, if the Git repository is clean, otherwise false.
        """
        directory = self.git_directory
        stdout: list[str] = []
        status = run_command(["git", "status", "--short"],
                             directory,
                             stdout=stdout)
        assert status == 0
        return bool(not stdout)

    def git_commit(self, reason: str) -> None:
        """ Commit the staged files to Git. """
        if not self.director.use_git:
            return
        directory = self.git_directory
        if _git_has_staged_files(directory):
            status = run_command(
                ["git", "commit", "-m", f"{self.item.uid}: {reason}"],
                directory)
            assert status == 0

    def _get_component(self, ctx: ItemGetValueContext) -> Any:
        if isinstance(self, PackageComponent):
            component = self
        else:
            assert self._component_stack[-1] is not None
            component = self._component_stack[-1]
        while True:
            try:
                args = "" if ctx.args is None else f":{ctx.args}"
                item, key_path, value = ctx.mapper.map(
                    f".:/{ctx.remaining_path}{args}", component.item)
            except ValueError:
                pass
            else:
                ctx.item = item
                ctx.path = key_path
                ctx.key_index = ""
                ctx.remaining_path = ""
                return value
            try:
                component = component.component
            except StopIteration as err:
                raise KeyError from err

    def _get_input(self, ctx: ItemGetValueContext) -> Any:
        return _get_input_or_output(ctx, self.input)

    def _get_output(self, ctx: ItemGetValueContext) -> Any:
        return _get_input_or_output(ctx, self.output)


class PackageComponent(BuildItem):
    """ Represents a package component. """

    def __init__(self,
                 director: "PackageBuildDirector",
                 item: Item,
                 mapper: None | BuildItemMapper = None) -> None:
        super().__init__(director, item, mapper)
        self.selection = ItemSelection(self.item.cache,
                                       self.item["enabled-set"],
                                       self.is_item_enabled)
        try:
            component = self.component
        except StopIteration:
            view = item.cache.top_view
        else:
            view = ItemView(component.view)
        self.view: ItemView = view

    def __getitem__(self, key: str) -> Any:
        component = self
        while True:
            if key in component.item:
                return component.substitute(component.item[key])
            try:
                component = component.component
            except StopIteration as err:
                raise KeyError(
                    f"{self.uid}: "
                    f"cannot get component value for '{key}': {err}") from err

    def run(self) -> None:
        self.description.add("Provide settings for the component.")

    def is_item_enabled(self, enabled_set: EnabledSet, item: Item) -> bool:
        """
        Return true, if the item is enabled for the enabled set, otherwise
        false.

        Where the item belongs to a component, the enabled set of the component
        is used.
        """
        try:
            component_item = build_item_input(item, "component")
        except KeyError:
            return is_enabled(enabled_set, item["enabled-by"])
        component = self.director[component_item.uid]
        assert isinstance(component, PackageComponent)
        enabled = is_enabled(component.selection.enabled_set,
                             item["enabled-by"])
        if not enabled:
            logging.info("%s: is disabled", item.uid)
        return enabled


class GenericPackageComponent(PackageComponent):
    """ Represents a generic package component. """

    def __init__(self,
                 director: "PackageBuildDirector",
                 item: Item,
                 mapper: None | BuildItemMapper = None) -> None:
        super().__init__(director, item, mapper)

        # Augment view with glossary terms
        with self.item.cache.selection(self.selection):
            with self.item.cache.view_scope(self.view):
                for glossary in self.item.parents("glossary"):
                    augment_glossary_terms(glossary, [])


class Redirection(BuildItem):
    """ Provides a build item redirection. """

    def target(self) -> BuildItem:
        """ Return the target build item of the redirection. """
        return self.input("redirection-target")


_ExportData = Callable[[Item, bool, bool], Any]


def export_data(item: Item, _present: bool, built_later: bool) -> Any:
    """ Export the item data using the presence and built later indicator. """
    data = copy.deepcopy(item.data)
    data.pop("workspace-hash", None)
    if built_later:
        for link in data["links"]:
            if link["role"] in ("input", "input-to"):
                link["hash"] = None
    return data


class BuildItemFactory:
    """
    Provides a factory to create build items for registered build item types.
    """

    def __init__(self) -> None:
        """ Initialize the dictionary of build steps """
        self.constructors: dict[str, Type[BuildItem]] = {}
        self._export_data: dict[str, _ExportData] = {}
        self._get_values: list[tuple[str, ItemGetValue]] = []

    def add_constructor(self, type_name: str, cls: Type[BuildItem]) -> None:
        """ Associate the build item constructor with the type name. """
        self.constructors[type_name] = cls
        cls.prepare_factory(self, type_name)

    def add_export_data(self, type_name: str,
                        export_data_method: _ExportData) -> None:
        """ Associate the export data method with the type name. """
        self._export_data[type_name] = export_data_method

    def add_get_value(self, type_path_key: str,
                      get_value: ItemGetValue) -> None:
        """ Add the get value method for the type key path. """
        self._get_values.append((type_path_key, get_value))

    def add_get_values_to_mapper(self, mapper: ItemMapper) -> None:
        """ Add the registered get value methods to the mapper. """
        for type_path_key, get_value in self._get_values:
            mapper.add_get_value(type_path_key, get_value)

    def create(self, director: "PackageBuildDirector",
               item: Item) -> BuildItem:
        """
        Create a build item for the item.

        The new build item will be assocated with the build director.
        """
        return self.constructors.get(item.type, BuildItem)(director, item)

    def export_data(self, item: Item, present: bool, build_order: int) -> Any:
        """ Export the item data using the presence indicator. """
        built_later = item.view.get("package-build-order",
                                    len(item.cache)) > build_order
        return self._export_data.get(item.type, export_data)(item, present,
                                                             built_later)


def _match(uid: str, patterns: Optional[list[str]]) -> bool:
    if patterns is None:
        return False
    return any(fnmatch.fnmatch(uid, pattern) for pattern in patterns)


def _gather_build_uids_of_package(item: Item, build_uids: set[str]) -> None:
    assert not item.is_proxy()
    if item.uid in build_uids:
        return
    build_uids.add(item.uid)
    with item.cache.selection(item.view["component"].selection):
        for dependency in itertools.chain(item.children("input"),
                                          item.parents("input-to")):
            _gather_build_uids_of_package(dependency, build_uids)


class PackageBuildDirector(dict):
    """
    The package build director contains the package build state and runs the
    build.
    """

    def __init__(self,
                 item_cache: ItemCache,
                 package_uid: str,
                 factory: BuildItemFactory,
                 use_git: Optional[bool] = False) -> None:
        self.item_cache = item_cache
        self.package_uid = package_uid
        self.factory = factory
        self.use_git = use_git
        self.submodules: tuple[str, ...] = tuple()
        item_cache.top_view.add_get_missing("component", self._get_component)

    def __missing__(self, uid: str) -> BuildItem:
        logging.info("%s: create build item", uid)
        return self.setdefault(uid,
                               self.factory.create(self, self.item_cache[uid]))

    @property
    def package(self) -> PackageComponent:
        """ Is the package component. """
        build_item = self[self.package_uid]
        assert isinstance(build_item, PackageComponent)
        return build_item

    def remove(self, uid: str) -> None:
        """
        Remove the build item associated with the UID from the director and
        the item cache.
        """
        self.pop(uid, None)
        self.item_cache.remove_item(uid)

    def add_submodule(self, submodule: str) -> None:
        """ Adds the submodule. """
        submodule = f"{submodule.rstrip('/')}/"
        self.submodules = self.submodules + (submodule, )

    def _get_component(self, item: Item) -> PackageComponent:
        try:
            component_item = build_item_input(item, "component")
        except KeyError:
            return self.package
        component = self[component_item.uid]
        assert isinstance(component, PackageComponent)
        return component

    def _gather_build_dependencies(self, item: Item,
                                   deps: dict[str, set[str]]) -> None:
        assert not item.is_proxy()
        uid = item.uid
        if uid in deps:
            return
        deps[uid] = set()
        component = item.view["component"]
        with self.item_cache.selection(component.selection):
            for dependency in itertools.chain(
                    item.parents(
                        ("input", "make", "weak-package-build-dependency")),
                    item.children(("input-to", "output"))):
                deps[uid].add(dependency.uid)
                self._gather_build_dependencies(dependency, deps)

    def _gather_ordered_build_uids_of_package(
            self, only: Optional[list[str]]) -> list[str]:
        item_cache = self.item_cache
        package = self.package.item
        build_uids: set[str] = set()
        _gather_build_uids_of_package(package, build_uids)
        if only is not None:
            build_only: set[str] = set()
            for uid in build_uids:
                if _match(uid, only):
                    build_only.add(uid)
            build_uids = build_only
        deps: dict[str, set[str]] = {}
        for uid in sorted(build_uids):
            self._gather_build_dependencies(item_cache[uid], deps)
        ordered_build_uids = list(
            graphlib.TopologicalSorter(deps).static_order())
        for uid in ordered_build_uids:
            logging.info("%s: depends on: %s", uid, sorted(deps[uid]))
        logging.info("%s: build order: %s", package.uid, ordered_build_uids)
        return ordered_build_uids

    def _build(self, method: str, **kwargs):
        only: Optional[list[str]] = kwargs.get("only", None)
        force: list[str] = kwargs.get("force", [])
        skip: Optional[list[str]] = kwargs.get("skip", None)
        item_cache = self.item_cache
        package = self.package
        with item_cache.selection(package.selection):
            build_uids = self._gather_ordered_build_uids_of_package(only)
            for build_order, uid in enumerate(build_uids):
                item = item_cache[uid]
                item.view["package-build-order"] = build_order
                component = item.view["component"]
                logging.info("%s: use component %s", uid, component.uid)
                with item_cache.selection(component.selection):
                    with item_cache.view_scope(component.view):
                        # Construct the builder even if building it is skipped
                        builder = self[uid]
                        is_forced = _match(uid, force)
                        if _match(uid, skip) and not is_forced:
                            logging.info(
                                "%s: build is skipped due to skip filter", uid)
                            continue
                        kwargs["component"] = component
                        kwargs["force"] = is_forced
                        getattr(builder, method)(**kwargs)

    def build_package(self,
                      only: Optional[list[str]] = None,
                      force: Optional[list[str]] = None,
                      skip: Optional[list[str]] = None) -> None:
        """ Build the package. """
        logging.info("%s: build the package", self.package_uid)
        self._build("build", only=only, force=force, skip=skip)
        logging.info("%s: finished building package", self.package_uid)

    def _build_only(self, item: Item, force_patterns: Optional[list[str]],
                    forced: set[str], seen: set[str],
                    build_order: int) -> None:
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-positional-arguments
        if item.uid in seen:
            return
        if _match(item.uid, force_patterns):
            forced.add(item.uid)
        is_forced = item.uid in forced
        logging.info("%s: prepare %sbuild", item.uid,
                     "forced " if is_forced else "")
        seen.add(item.uid)
        is_output = False
        for link in itertools.chain(
                item.links_to_children(("input-to", "output")),
                item.links_to_parents("input")):
            if link.role == "output":
                is_output = True
                if is_forced:
                    forced.add(link.item.uid)
            self._build_only(link.item, force_patterns, forced, seen,
                             build_order - 1)
        if not is_output:
            item.view["package-build-order"] = build_order
            component = item.view["component"]
            logging.info("%s: use component %s", item.uid, component.uid)
            with self.item_cache.selection(component.selection):
                with self.item_cache.view_scope(component.view):
                    build_item = self[item.uid]
                    is_necessary = build_item.is_build_necessary()
                    if is_necessary:
                        logging.info("%s: build is necessary", item.uid)
                    if is_forced:
                        logging.info("%s: build is forced", item.uid)
                    if is_necessary or is_forced:
                        for dependency in itertools.chain(
                                item.children("input-to"),
                                item.parents("input")):
                            dependency_build_item = self[dependency.uid]
                            if not dependency_build_item.is_present():
                                logging.info(
                                    "%s: dependency is not present: %s",
                                    item.uid, dependency.uid)
                                forced.add(dependency.uid)
                                self._build_only(dependency, force_patterns,
                                                 forced, set(),
                                                 build_order - 1)
                        build_item.do_run()
        logging.info("%s: building done", item.uid)

    def build_only(self,
                   uids: str | list[str],
                   force_patterns: Optional[list[str]] = None) -> None:
        """
        Build the items associated with the UIDs and their dependencies if
        necessary.
        """
        with self.item_cache.selection(self.package.selection):
            seen: set[str] = set()
            for uid in to_iterable(uids):
                self._build_only(self.item_cache[uid], force_patterns, set(),
                                 seen, 0)

    def add_build_description(self, content: SphinxContent,
                              build_uids: list[str]) -> None:
        """ Add the build description of the build items to the content. """
        self._build("add_build_section", content=content, only=build_uids)

.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2023, 2026 embedded brains GmbH & Co. KG

.. subprocess hide-cwd
${.:/subprocess:args=hide-cwd 1 2,hide_cwd=1,cwd=%(.:/component/build-directory)}
.. subprocess hide-output
${.:/subprocess:args=hide-output 3 4,strip_cwd=%(.:/component/prefix-directory),shell=0,hide_output=1,cwd=%(.:/component/build-directory)}
.. subprocess hide
${.:/subprocess:args=hide 5 6,hide=1,check=0}
.. subprocess stderr
${.:/subprocess:args=stderr,stderr=%(.:/component/build-directory)/stderr,cwd=%(.:/component/build-directory)}
.. subprocess stdout
${.:/subprocess:args=stdout,stdout=%(.:/component/build-directory)/stdout,cwd=%(.:/component/build-directory)}
.. subprocess stdin stderr
${.:/subprocess:args=stdin stderr,stdin=%(.:/component/build-directory)/stderr,cwd=%(.:/component/build-directory)}
.. subprocess stdin stdout
${.:/subprocess:args=stdin stdout,stdin=%(.:/component/build-directory)/stdout,cwd=%(.:/component/build-directory)}
.. subprocess no-output
${.:/subprocess:args=no-output,cwd=%(/pkg/deployment/doc-package-manual:/directory),indent=1}
.. subprocess hidden_args
${.:/subprocess:args=a b c \\\%\(\)\0\a\b\c\f\n\r\s\t\v,hidden_args=hidden,hide_args=1,encoding=latin-1}
.. archive basename
${.:/input/archive/file:basename}
.. archive sha512
${.:/input/archive/sha512}
.. pkg-config
${.:/pkg-config}
.. verify-package basename
${.:/input/verify-package/file:basename}
.. verify-package help
${.:/subprocess:args=./%(.:/input/verify-package/file:basename) --help,cwd=%(.:/input/verify-package/file:dirname)}
.. object-size
${.:/object-size:/rtems/task/obj}
.. benchmark-variants-list
${.:/benchmark-variants-list}
.. memory-benchmarks
${.:/memory-benchmarks}
.. memory-benchmark-reference
${.:/memory-benchmark-reference:/rtems/val/mem-basic}
.. memory-benchmark-based-on-reference
${.:/memory-benchmark-based-on-reference:/rtems/val/mem-basic}
.. memory-benchmark-section
${.:/memory-benchmark-section:/rtems/val/mem-basic:.text}
.. memory-benchmark-compare-section
${.:/memory-benchmark-compare-section:/rtems/val/mem-basic:/rtems/val/mem-basic:.text}
.. memory-benchmark-variants-table
${.:/memory-benchmark-variants-table}
.. performance-variants-table
${.:/performance-variants-table}
.. repositories
${.:/repositories}
.. pre-qualified-interfaces
${.:/pre-qualified-interfaces}
.. targets
${.:/targets}
.. change-list
${.:/change-list}
.. open-issues
${.:/open-issues}
.. license-info
${.:/license-info}
.. clear-copyrights-by-license
${.:/clear-copyrights-by-license}
.. license-info
${.:/license-info}
.. build-description
${.:/build-description:0:/pkg/deployment/doc-package-manual}

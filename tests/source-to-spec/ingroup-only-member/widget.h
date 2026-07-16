#ifndef WIDGET_H
#define WIDGET_H
#include <stddef.h>

/**
 * @defgroup WidgetAPI Widget API
 * @brief This is the Widget API.
 */

/**
 * @brief Sets the size of the widget referenced by @a w.
 * @param[in,out] w is the pointer to the widget object.
 * @param[in] size is the new size of the widget.
 * @ingroup WidgetAPI
 */
void widget_set_size( struct widget *w, size_t size );
#endif

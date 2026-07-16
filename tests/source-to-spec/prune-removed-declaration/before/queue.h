#ifndef QUEUE_H
#define QUEUE_H
#include <stddef.h>

/**
 * @defgroup QueueAPI Queue API
 * @brief This is the Queue API.
 */

/**
 * @file
 * @ingroup QueueAPI
 */

/**
 * @brief Creates a queue.
 * @param capacity is the queue capacity.
 */
void *queue_create( size_t capacity );

/**
 * @brief Destroys the queue referenced by @a q.
 * @param q is the queue to destroy.
 */
void queue_destroy( void *q );
#endif

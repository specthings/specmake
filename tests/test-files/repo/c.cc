/**
 * @file
 *
 * @ingroup Blub
 *
 * @brief The c.cc brief.
 *
 * The c.cc description.
 */

/**
 * @brief The N brief.
 *
 * The N description.
 */
namespace N {
  /**
   * @brief The C brief.
   *
   * The C description.
   */
  class C {
    public:
      /**
       * @brief The C constructor brief.
       *
       * The C constructor description.
       */
      C() : a(0)
      {
        b();
      }

      /**
       * @brief The a member brief.
       *
       * The a member description.
       */
      int a;

      /**
       * @brief The b method brief.
       *
       * The b method description.
       */
      int b()
      {
        a = 1;
      }
  };
}

/**
 * @file
 *
 * @ingroup UnspecGroup
 *
 * @brief The unspec.h brief.
 *
 * The unspec.h description.
 */

/**
 * @defgroup UnspecGroup UnspecGroup
 *
 * @ingroup Blub
 *
 * @brief The UnspecGroup brief.
 *
 * The UnspecGroup description.
 *
 * @{
 */

/**
 * @brief The UnspecDefine brief.
 *
 * The UnspecDefine description.
 */
#define UnspecDefine 123

/**
 * @brief The UnspecMacro brief.
 *
 * The UnspecMacro description.
 */
#define UnspecMacro(x) ((x) * 456)

/**
 * @brief The UnspecEnum brief.
 *
 * The UnspecEnum description.
 */
enum UnspecEnum {
  /**
   * @brief The UnspecEnumerator brief.
   *
   * The UnspecEnumerator description.
   */
  UnspecEnumerator
};

/**
 * @brief The UnspecStruct brief.
 *
 * The UnspecStruct description.
 */
struct UnspecStruct {
  /**
   * @ingroup UnspecGroup
   *
   * @brief The UnspecStruct member brief.
   *
   * The UnspecStruct member description.
   */
  int a;
};

/**
 * @brief The UnspecUnion brief.
 *
 * The UnspecUnion description.
 */
union UnspecUnion {
  /**
   * @brief The UnspecUnion member brief.
   *
   * The UnspecUnion member description.
   */
  int a;
};

/**
 * @brief The UnspecFunction brief.
 *
 * The UnspecFunction description.
 *
 * @param param is parameter.
 */
int UnspecFunction(int param);

/**
 * @brief The UnspecObject brief.
 *
 * The UnspecObject description.
 */
extern int UnspecObject;

/**
 * @brief The UnspecTypedef brief.
 *
 * The UnspecTypedef description.
 */
typedef struct UnspecStruct UnspecTypedef;

/** @} */

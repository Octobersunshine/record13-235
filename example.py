from concrete_mix import ConcreteMixCalculator, get_concrete_mix


def basic_usage():
    print("=" * 60)
    print("基本用法示例")
    print("=" * 60)

    calc = ConcreteMixCalculator()

    print("\n1. C30 混凝土配比:")
    result_c30 = calc.calculate("C30")
    print(result_c30)

    print("\n2. C40 混凝土配比:")
    result_c40 = calc.calculate("C40")
    print(result_c40)


def custom_parameters():
    print("\n" + "=" * 60)
    print("自定义参数示例")
    print("=" * 60)

    print("\n1. 使用 P.O 52.5 水泥的 C40 配比:")
    calc = ConcreteMixCalculator(cement_strength=52.5)
    print(calc.calculate("C40"))

    print("\n2. 使用卵石骨料的 C30 配比:")
    calc = ConcreteMixCalculator(aggregate_type="pebble")
    print(calc.calculate("C30"))

    print("\n3. 大坍落度 (160mm) C30 配比:")
    calc = ConcreteMixCalculator(slump=160)
    print(calc.calculate("C30"))


def dictionary_output():
    print("\n" + "=" * 60)
    print("字典格式输出示例")
    print("=" * 60)

    result = get_concrete_mix("C30")
    print("\nC30 配比字典:")
    for key, value in result.items():
        print(f"  {key}: {value}")

    result = get_concrete_mix("C40")
    print("\nC40 配比字典:")
    for key, value in result.items():
        print(f"  {key}: {value}")


def batch_calculation():
    print("\n" + "=" * 60)
    print("批量计算示例")
    print("=" * 60)

    grades = ["C25", "C30", "C35", "C40", "C45", "C50"]
    calc = ConcreteMixCalculator()

    print(f"\n{'等级':<6} {'水泥':>8} {'砂':>8} {'石':>8} {'水':>8} {'水灰比':>8}")
    print("-" * 60)

    for grade in grades:
        result = calc.calculate(grade)
        print(
            f"{grade:<6} {result.cement:>8.1f} {result.sand:>8.1f} "
            f"{result.gravel:>8.1f} {result.water:>8.1f} "
            f"{result.water_cement_ratio:>8.3f}"
        )


def error_handling():
    print("\n" + "=" * 60)
    print("错误处理示例")
    print("=" * 60)

    calc = ConcreteMixCalculator()

    try:
        calc.calculate("C100")
    except ValueError as e:
        print(f"\n预期的错误: {e}")


if __name__ == "__main__":
    basic_usage()
    custom_parameters()
    dictionary_output()
    batch_calculation()
    error_handling()

    print("\n" + "=" * 60)
    print("所有示例运行完成!")
    print("=" * 60)

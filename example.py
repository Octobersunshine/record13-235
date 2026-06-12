from concrete_mix import ConcreteMixCalculator, get_concrete_mix


def compare_cement_grades():
    print("=" * 70)
    print("不同水泥标号配比对比分析 (PO32.5 vs PO42.5)")
    print("=" * 70)

    calc_325 = ConcreteMixCalculator(cement_strength=32.5)
    calc_425 = ConcreteMixCalculator(cement_strength=42.5)

    grades = ["C25", "C30", "C35", "C40", "C45"]

    print(f"\n{'等级':<6} {'水泥标号':<10} {'水泥(kg)':>9} {'砂(kg)':>9} {'石(kg)':>9} "
          f"{'水(kg)':>8} {'水灰比':>7} {'警告':>8}")
    print("-" * 100)

    for g in grades:
        for name, calc in [("PO32.5", calc_325), ("PO42.5", calc_425)]:
            r = calc.calculate(g)
            warn_count = len(r.warnings)
            warn_str = f"  {warn_count}" if warn_count > 0 else "   -"
            print(
                f"{g:<6} {name:<10} {r.cement:>9.1f} {r.sand:>9.1f} {r.gravel:>9.1f} "
                f"{r.water:>8.1f} {r.water_cement_ratio:>7.3f} {warn_str:>8}"
            )
            if r.warnings:
                for w in r.warnings:
                    print(f"        >> 警告: {w}")
        print()


def basic_usage():
    print("\n" + "=" * 70)
    print("基本用法示例")
    print("=" * 70)

    calc = ConcreteMixCalculator(cement_strength=42.5)

    print("\n1. C30 混凝土配比 (PO42.5):")
    result = calc.calculate("C30")
    print(result)

    print("\n2. C40 混凝土配比 (PO42.5):")
    result = calc.calculate("C40")
    print(result)


def po325_examples():
    print("\n" + "=" * 70)
    print("P.O 32.5 水泥配比例子")
    print("=" * 70)

    calc = ConcreteMixCalculator(cement_strength=32.5)

    print("\n1. P.O 32.5 配置 C30:")
    print(calc.calculate("C30"))

    print("\n2. P.O 32.5 配置 C40 (应有警告提示):")
    print(calc.calculate("C40"))


def custom_parameters():
    print("\n" + "=" * 70)
    print("自定义参数示例")
    print("=" * 70)

    print("\n1. 使用 P.O 52.5 水泥配置 C50:")
    calc = ConcreteMixCalculator(cement_strength=52.5)
    print(calc.calculate("C50"))

    print("\n2. 使用卵石骨料的 C30 配比 (PO42.5):")
    calc = ConcreteMixCalculator(cement_strength=42.5, aggregate_type="pebble")
    print(calc.calculate("C30"))

    print("\n3. 大坍落度 (160mm) C30 配比 (PO42.5):")
    calc = ConcreteMixCalculator(cement_strength=42.5, slump=160)
    print(calc.calculate("C30"))


def dictionary_output():
    print("\n" + "=" * 70)
    print("字典格式输出示例")
    print("=" * 70)

    result = get_concrete_mix("C30", cement_strength=42.5)
    print("\nC30 + PO42.5 配比字典:")
    for key, value in result.items():
        print(f"  {key}: {value}")

    result = get_concrete_mix("C30", cement_strength=32.5)
    print("\nC30 + PO32.5 配比字典:")
    for key, value in result.items():
        print(f"  {key}: {value}")


def batch_calculation():
    print("\n" + "=" * 70)
    print("多强度等级批量计算对比 (PO42.5)")
    print("=" * 70)

    grades = ["C15", "C20", "C25", "C30", "C35", "C40", "C45", "C50"]
    calc = ConcreteMixCalculator(cement_strength=42.5)

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
    print("\n" + "=" * 70)
    print("错误处理示例")
    print("=" * 70)

    calc = ConcreteMixCalculator()

    try:
        calc.calculate("C100")
    except ValueError as e:
        print(f"\n预期的错误: {e}")


if __name__ == "__main__":
    compare_cement_grades()
    basic_usage()
    po325_examples()
    custom_parameters()
    dictionary_output()
    batch_calculation()
    error_handling()

    print("\n" + "=" * 70)
    print("所有示例运行完成!")
    print("=" * 70)

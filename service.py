import argparse
import json
from typing import Dict

from concrete_mix import ConcreteMixCalculator, get_concrete_mix


def run_api_server(host: str = "0.0.0.0", port: int = 5000) -> None:
    try:
        from flask import Flask, request, jsonify
    except ImportError:
        print("Flask 未安装，请运行: pip install flask")
        return

    app = Flask(__name__)
    calculator = ConcreteMixCalculator()

    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "ok", "service": "concrete-mix-calculator"})

    @app.route("/api/calculate", methods=["POST"])
    def calculate():
        data = request.get_json()
        if not data or "strength_grade" not in data:
            return jsonify({"error": "缺少必需参数: strength_grade"}), 400

        strength_grade = data["strength_grade"].upper()
        cement_strength = data.get("cement_strength", 42.5)
        aggregate_type = data.get("aggregate_type", "gravel")
        slump = data.get("slump", 80)
        assumed_weight = data.get("assumed_weight", 2400.0)

        try:
            calc = ConcreteMixCalculator(
                cement_strength=cement_strength,
                aggregate_type=aggregate_type,
                slump=slump,
                assumed_weight=assumed_weight,
            )
            result = calc.calculate(strength_grade)
            return jsonify({"code": 0, "message": "success", "data": result.to_dict()})
        except ValueError as e:
            return jsonify({"code": 1, "message": str(e)}), 400
        except Exception as e:
            return jsonify({"code": 2, "message": f"服务器内部错误: {str(e)}"}), 500

    @app.route("/api/batch", methods=["POST"])
    def batch_calculate():
        data = request.get_json()
        if not data or "grades" not in data:
            return jsonify({"error": "缺少必需参数: grades"}), 400

        grades = data["grades"]
        results = {}
        errors = []

        for grade in grades:
            try:
                result = get_concrete_mix(grade)
                results[grade.upper()] = result
            except ValueError as e:
                errors.append({grade: str(e)})

        return jsonify(
            {"code": 0, "data": results, "errors": errors if errors else None}
        )

    print(f"混凝土配比计算服务启动于 http://{host}:{port}")
    print("API 端点:")
    print("  POST /api/calculate  - 单种强度等级计算")
    print("  POST /api/batch      - 批量计算")
    print("  GET  /health         - 健康检查")
    app.run(host=host, port=port)


def run_cli(
    strength_grade: str,
    output_format: str = "text",
    cement_strength: float = 42.5,
) -> None:
    calculator = ConcreteMixCalculator(cement_strength=cement_strength)
    try:
        result = calculator.calculate(strength_grade)
        if output_format == "json":
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        else:
            print(result)
    except ValueError as e:
        print(f"错误: {e}")


def main():
    parser = argparse.ArgumentParser(description="混凝土配比计算服务")
    subparsers = parser.add_subparsers(dest="command", help="命令类型")

    api_parser = subparsers.add_parser("api", help="启动 HTTP API 服务")
    api_parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    api_parser.add_argument("--port", type=int, default=5000, help="监听端口")

    cli_parser = subparsers.add_parser("calc", help="命令行计算")
    cli_parser.add_argument("grade", help="强度等级，如 C30, C40")
    cli_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="输出格式",
    )
    cli_parser.add_argument(
        "--cement",
        type=float,
        default=42.5,
        help="水泥标号强度，如 32.5, 42.5, 52.5 (默认: 42.5)",
    )

    args = parser.parse_args()

    if args.command == "api":
        run_api_server(host=args.host, port=args.port)
    elif args.command == "calc":
        run_cli(args.grade, output_format=args.format, cement_strength=args.cement)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

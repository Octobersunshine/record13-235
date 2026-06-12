from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class MoistureCorrection:
    sand_moisture_pct: float
    gravel_moisture_pct: float
    sand_water: float
    gravel_water: float
    adjusted_sand: float
    adjusted_gravel: float
    adjusted_water: float

    def to_dict(self) -> Dict:
        return {
            "sand_moisture_pct": round(self.sand_moisture_pct, 1),
            "gravel_moisture_pct": round(self.gravel_moisture_pct, 1),
            "sand_water": round(self.sand_water, 1),
            "gravel_water": round(self.gravel_water, 1),
            "adjusted_sand": round(self.adjusted_sand, 1),
            "adjusted_gravel": round(self.adjusted_gravel, 1),
            "adjusted_water": round(self.adjusted_water, 1),
        }

    def __str__(self) -> str:
        return (
            f"  含水校正:\n"
            f"    砂含水率: {self.sand_moisture_pct:.1f}%  →  "
            f"砂中含水量: {self.sand_water:.1f} kg/m³  →  "
            f"校正后湿砂: {self.adjusted_sand:.1f} kg/m³\n"
            f"    石含水率: {self.gravel_moisture_pct:.1f}%  →  "
            f"石中含水量: {self.gravel_water:.1f} kg/m³  →  "
            f"校正后湿石: {self.adjusted_gravel:.1f} kg/m³\n"
            f"    校正后用水量: {self.adjusted_water:.1f} kg/m³ "
            f"(原用水量扣除砂石含水)"
        )


@dataclass
class MixResult:
    cement: float
    sand: float
    gravel: float
    water: float
    water_cement_ratio: float
    design_strength: str
    total_weight: float
    cement_grade: str
    warnings: List[str] = field(default_factory=list)
    moisture_correction: Optional[MoistureCorrection] = None

    def to_dict(self) -> Dict:
        result = {
            "cement": round(self.cement, 1),
            "sand": round(self.sand, 1),
            "gravel": round(self.gravel, 1),
            "water": round(self.water, 1),
            "water_cement_ratio": round(self.water_cement_ratio, 3),
            "total_weight": round(self.total_weight, 1),
            "design_strength": self.design_strength,
            "cement_grade": self.cement_grade,
            "warnings": self.warnings if self.warnings else None,
            "moisture_correction": (
                self.moisture_correction.to_dict()
                if self.moisture_correction
                else None
            ),
        }
        if self.moisture_correction:
            mc = self.moisture_correction
            result["adjusted_sand"] = round(mc.adjusted_sand, 1)
            result["adjusted_gravel"] = round(mc.adjusted_gravel, 1)
            result["adjusted_water"] = round(mc.adjusted_water, 1)
        return result

    def __str__(self) -> str:
        lines = [
            f"混凝土配合比 ({self.design_strength}, {self.cement_grade}):",
            f"  水泥: {self.cement:.1f} kg/m³",
            f"  砂:   {self.sand:.1f} kg/m³",
            f"  石:   {self.gravel:.1f} kg/m³",
            f"  水:   {self.water:.1f} kg/m³",
            f"  水灰比: {self.water_cement_ratio:.3f}",
            f"  总容重: {self.total_weight:.1f} kg/m³",
            f"  比例: 水泥:砂:石:水 = 1 : {self.sand/self.cement:.2f} : "
            f"{self.gravel/self.cement:.2f} : {self.water/self.cement:.2f}",
        ]
        if self.moisture_correction:
            lines.append(str(self.moisture_correction))
        if self.warnings:
            lines.append("  注意事项:")
            for w in self.warnings:
                lines.append(f"    - {w}")
        return "\n".join(lines)


class ConcreteMixCalculator:
    STRENGTH_MAP = {
        "C15": 15.0, "C20": 20.0, "C25": 25.0,
        "C30": 30.0, "C35": 35.0, "C40": 40.0,
        "C45": 45.0, "C50": 50.0, "C55": 55.0, "C60": 60.0,
    }

    CEMENT_GRADE_MAP = {
        32.5: "P.O 32.5",
        42.5: "P.O 42.5",
        52.5: "P.O 52.5",
        62.5: "P.O 62.5",
    }

    CEMENT_STRENGTH_COEFF = {
        32.5: 1.15,
        42.5: 1.13,
        52.5: 1.10,
        62.5: 1.08,
    }

    MAX_W_C_RATIO = {
        "C15": 0.75, "C20": 0.70, "C25": 0.65,
        "C30": 0.60, "C35": 0.55, "C40": 0.50,
        "C45": 0.46, "C50": 0.42, "C55": 0.38, "C60": 0.34,
    }

    MIN_W_C_RATIO = 0.32

    CEMENT_GRADE_MAX_STRENGTH = {
        32.5: "C35",
        42.5: "C55",
        52.5: "C60",
        62.5: "C60",
    }

    def __init__(
        self,
        cement_strength: float = 42.5,
        aggregate_type: str = "gravel",
        slump: int = 80,
        sand_fineness: float = 2.6,
        assumed_weight: float = 2400.0,
    ):
        self.cement_strength = cement_strength
        self.aggregate_type = aggregate_type
        self.slump = slump
        self.sand_fineness = sand_fineness
        self.assumed_weight = assumed_weight

        self.cement_grade = self.CEMENT_GRADE_MAP.get(
            cement_strength, f"P.O {cement_strength}"
        )
        self.cement_strength_coeff = self._get_cement_strength_coeff()

        if aggregate_type == "gravel":
            self.alpha_a = 0.53
            self.alpha_b = 0.20
        else:
            self.alpha_a = 0.49
            self.alpha_b = 0.13

    def _get_cement_strength_coeff(self) -> float:
        if self.cement_strength in self.CEMENT_STRENGTH_COEFF:
            return self.CEMENT_STRENGTH_COEFF[self.cement_strength]
        if self.cement_strength < 35.0:
            return 1.16
        elif self.cement_strength < 47.5:
            return 1.13
        elif self.cement_strength < 57.5:
            return 1.10
        else:
            return 1.08

    def _get_std_deviation(self, fcu_k: float) -> float:
        if fcu_k < 30:
            return 4.0
        elif fcu_k <= 50:
            return 5.0
        else:
            return 6.0

    def _get_water_content(self, fcu_k: float, water_cement_ratio: float) -> float:
        base_water = 180.0
        if self.slump > 100:
            base_water += (self.slump - 100) // 20 * 5
        if fcu_k >= 40:
            base_water -= 5
        if water_cement_ratio < 0.42:
            base_water -= 5
        elif water_cement_ratio > 0.60:
            base_water += 5
        return base_water

    def _get_sand_ratio(self, fcu_k: float, w_c: float) -> float:
        base_ratio = 0.33
        if w_c < 0.40:
            base_ratio -= 0.02
        elif w_c > 0.50:
            base_ratio += 0.02
        if fcu_k >= 40:
            base_ratio -= 0.01
        if self.aggregate_type == "pebble":
            base_ratio -= 0.02
        return max(0.28, min(0.42, base_ratio))

    def _get_min_cement(self, fcu_k: float) -> float:
        if fcu_k < 20:
            base = 240
        elif fcu_k < 30:
            base = 260
        elif fcu_k < 40:
            base = 280
        else:
            base = 300
        if self.cement_strength < 35.0:
            base += 20
        return base

    def _get_max_cement(self, fcu_k: float) -> float:
        if fcu_k < 30:
            return 400
        elif fcu_k < 40:
            return 450
        else:
            return 550

    def calculate(
        self,
        strength_grade: str,
        sand_moisture: float = 0.0,
        gravel_moisture: float = 0.0,
    ) -> MixResult:
        strength_grade = strength_grade.upper()
        if strength_grade not in self.STRENGTH_MAP:
            raise ValueError(
                f"不支持的强度等级: {strength_grade}. "
                f"支持的等级: {', '.join(self.STRENGTH_MAP.keys())}"
            )

        warnings = []
        fcu_k = self.STRENGTH_MAP[strength_grade]
        fcu_k_value = fcu_k

        max_grade = self.CEMENT_GRADE_MAX_STRENGTH.get(self.cement_strength, "C40")
        max_fcu_k = self.STRENGTH_MAP.get(max_grade, 40.0)
        if fcu_k_value > max_fcu_k:
            warnings.append(
                f"建议使用更高标号水泥（当前 {self.cement_grade} 不建议配置 {strength_grade}）"
            )

        sigma = self._get_std_deviation(fcu_k_value)
        fcu_o = fcu_k_value + 1.645 * sigma

        fce = self.cement_strength * self.cement_strength_coeff
        w_c = (self.alpha_a * fce) / (fcu_o + self.alpha_a * self.alpha_b * fce)

        max_w_c = self.MAX_W_C_RATIO.get(strength_grade, 0.60)
        if w_c > max_w_c:
            w_c = max_w_c
            warnings.append(
                f"水灰比已调整至耐久性限制上限 {max_w_c:.2f}（理论值更大）"
            )
        if w_c < self.MIN_W_C_RATIO:
            w_c = self.MIN_W_C_RATIO
            warnings.append(
                f"水灰比已调整至施工下限 {self.MIN_W_C_RATIO}（理论值过小）"
            )

        water = self._get_water_content(fcu_k_value, w_c)
        cement = water / w_c

        min_cement = self._get_min_cement(fcu_k_value)
        max_cement = self._get_max_cement(fcu_k_value)

        if cement < min_cement:
            cement = min_cement
            w_c = water / cement
            warnings.append(
                f"水泥用量已调整至最小值 {min_cement:.0f} kg/m³（耐久性要求）"
            )
        if cement > max_cement:
            cement = max_cement
            w_c = water / cement
            warnings.append(
                f"水泥用量已调整至最大值 {max_cement:.0f} kg/m³（施工和经济性限制）"
            )

        if w_c > max_w_c:
            water = cement * max_w_c
            w_c = max_w_c
            if "水灰比已调整至耐久性限制上限" not in str(warnings):
                warnings.append(
                    f"用水量已根据耐久性水灰比上限 {max_w_c:.2f} 调整"
                )

        sand_ratio = self._get_sand_ratio(fcu_k_value, w_c)
        aggregate_total = self.assumed_weight - cement - water
        sand = aggregate_total * sand_ratio
        gravel = aggregate_total * (1 - sand_ratio)

        total_weight = cement + sand + gravel + water

        moisture_correction = None
        if sand_moisture > 0 or gravel_moisture > 0:
            if sand_moisture < 0 or sand_moisture > 15:
                raise ValueError(
                    f"砂含水率不合理: {sand_moisture}%，有效范围: 0~15%"
                )
            if gravel_moisture < 0 or gravel_moisture > 10:
                raise ValueError(
                    f"石含水率不合理: {gravel_moisture}%，有效范围: 0~10%"
                )

            sand_water = sand * sand_moisture / 100.0
            gravel_water = gravel * gravel_moisture / 100.0
            adjusted_sand = sand + sand_water
            adjusted_gravel = gravel + gravel_water
            adjusted_water = water - sand_water - gravel_water

            if adjusted_water < 0:
                warnings.append(
                    f"砂石含水量 ({sand_water + gravel_water:.1f} kg/m³) "
                    f"超过设计用水量 ({water:.1f} kg/m³)，请核实含水率数据"
                )
                adjusted_water = 0.0

            moisture_correction = MoistureCorrection(
                sand_moisture_pct=sand_moisture,
                gravel_moisture_pct=gravel_moisture,
                sand_water=sand_water,
                gravel_water=gravel_water,
                adjusted_sand=adjusted_sand,
                adjusted_gravel=adjusted_gravel,
                adjusted_water=adjusted_water,
            )

        return MixResult(
            cement=cement,
            sand=sand,
            gravel=gravel,
            water=water,
            water_cement_ratio=w_c,
            design_strength=strength_grade,
            total_weight=total_weight,
            cement_grade=self.cement_grade,
            warnings=warnings,
            moisture_correction=moisture_correction,
        )


def get_concrete_mix(
    strength_grade: str,
    cement_strength: float = 42.5,
    aggregate_type: str = "gravel",
    sand_moisture: float = 0.0,
    gravel_moisture: float = 0.0,
) -> Dict:
    calculator = ConcreteMixCalculator(
        cement_strength=cement_strength,
        aggregate_type=aggregate_type,
    )
    result = calculator.calculate(
        strength_grade,
        sand_moisture=sand_moisture,
        gravel_moisture=gravel_moisture,
    )
    return result.to_dict()

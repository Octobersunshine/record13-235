from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class MixResult:
    cement: float
    sand: float
    gravel: float
    water: float
    water_cement_ratio: float
    design_strength: str
    total_weight: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "cement": round(self.cement, 1),
            "sand": round(self.sand, 1),
            "gravel": round(self.gravel, 1),
            "water": round(self.water, 1),
            "water_cement_ratio": round(self.water_cement_ratio, 3),
            "total_weight": round(self.total_weight, 1),
            "design_strength": self.design_strength,
        }

    def __str__(self) -> str:
        return (
            f"混凝土配合比 ({self.design_strength}):\n"
            f"  水泥: {self.cement:.1f} kg/m³\n"
            f"  砂:   {self.sand:.1f} kg/m³\n"
            f"  石:   {self.gravel:.1f} kg/m³\n"
            f"  水:   {self.water:.1f} kg/m³\n"
            f"  水灰比: {self.water_cement_ratio:.3f}\n"
            f"  总容重: {self.total_weight:.1f} kg/m³\n"
            f"  比例: 水泥:砂:石:水 = 1 : {self.sand/self.cement:.2f} : "
            f"{self.gravel/self.cement:.2f} : {self.water/self.cement:.2f}"
        )


class ConcreteMixCalculator:
    STRENGTH_MAP = {
        "C15": 15.0, "C20": 20.0, "C25": 25.0,
        "C30": 30.0, "C35": 35.0, "C40": 40.0,
        "C45": 45.0, "C50": 50.0, "C55": 55.0, "C60": 60.0,
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

        if aggregate_type == "gravel":
            self.alpha_a = 0.53
            self.alpha_b = 0.20
        else:
            self.alpha_a = 0.49
            self.alpha_b = 0.13

    def _get_std_deviation(self, fcu_k: float) -> float:
        if fcu_k < 30:
            return 4.0
        elif fcu_k <= 50:
            return 5.0
        else:
            return 6.0

    def _get_water_content(self, fcu_k: float) -> float:
        base_water = 175.0
        if self.slump > 100:
            base_water += (self.slump - 100) // 20 * 5
        if fcu_k >= 40:
            base_water -= 5
        return base_water

    def _get_sand_ratio(self, fcu_k: float, w_c: float) -> float:
        base_ratio = 0.33
        if w_c < 0.4:
            base_ratio -= 0.02
        elif w_c > 0.5:
            base_ratio += 0.02
        if fcu_k >= 40:
            base_ratio -= 0.01
        return base_ratio

    def calculate(self, strength_grade: str) -> MixResult:
        strength_grade = strength_grade.upper()
        if strength_grade not in self.STRENGTH_MAP:
            raise ValueError(
                f"不支持的强度等级: {strength_grade}. "
                f"支持的等级: {', '.join(self.STRENGTH_MAP.keys())}"
            )

        fcu_k = self.STRENGTH_MAP[strength_grade]
        sigma = self._get_std_deviation(fcu_k)
        fcu_o = fcu_k + 1.645 * sigma

        fce = self.cement_strength * 1.13
        w_c = (self.alpha_a * fce) / (fcu_o + self.alpha_a * self.alpha_b * fce)

        water = self._get_water_content(fcu_k)
        cement = water / w_c

        min_cement = 260 if fcu_k < 30 else 280
        max_cement = 550
        if cement < min_cement:
            cement = min_cement
            water = cement * w_c
        if cement > max_cement:
            cement = max_cement
            w_c = water / cement

        sand_ratio = self._get_sand_ratio(fcu_k, w_c)
        aggregate_total = self.assumed_weight - cement - water
        sand = aggregate_total * sand_ratio
        gravel = aggregate_total * (1 - sand_ratio)

        total_weight = cement + sand + gravel + water

        return MixResult(
            cement=cement,
            sand=sand,
            gravel=gravel,
            water=water,
            water_cement_ratio=w_c,
            design_strength=strength_grade,
            total_weight=total_weight,
        )


def get_concrete_mix(
    strength_grade: str,
    cement_strength: float = 42.5,
    aggregate_type: str = "gravel",
) -> Dict[str, float]:
    calculator = ConcreteMixCalculator(
        cement_strength=cement_strength,
        aggregate_type=aggregate_type,
    )
    result = calculator.calculate(strength_grade)
    return result.to_dict()

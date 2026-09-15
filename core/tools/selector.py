# ========== selector.py ==========
# Mikasa AI 7.x — Smart Tool Selection & Explanation Engine
# Multi-Factor Candidate Scoring, Observability Explanation & Safe Fallbacks

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from core.intelligence.types import RiskLevel
from core.tools.contract import ToolContract2, ToolHealth

logger = logging.getLogger(__name__)


@dataclass
class ToolSelectionResult:
    """Asbob tanlash natijasi va tushuntirishi (Observability)"""
    tool: Optional[ToolContract2]
    score: float = 0.0
    explanation: str = ""
    required_capability: str = ""
    candidate_tools: List[str] = field(default_factory=list)
    fallback_tool: Optional[ToolContract2] = None
    scoring_breakdown: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "selected_tool": self.tool.name if self.tool else None,
            "score": round(self.score, 3),
            "explanation": self.explanation,
            "required_capability": self.required_capability,
            "candidate_tools": self.candidate_tools,
            "fallback_tool": self.fallback_tool.name if self.fallback_tool else None,
            "scoring_breakdown": {k: round(v, 3) for k, v in self.scoring_breakdown.items()},
        }


class SmartToolSelector:
    """
    Qobiliyat va kontekstga qarab eng mos asbobni tanlash dvigateli.
    Nega aynan shu asbob tanlanganini (explanation) batafsil hisoblaydi.
    """

    @staticmethod
    def select_best_tool(
        required_capability: str,
        candidate_tools: List[ToolContract2],
        context: Optional[Any] = None,
        candidate_params: Optional[Dict[str, Any]] = None,
        prefer_low_risk: bool = True
    ) -> ToolSelectionResult:
        """
        Nomzod asboblar orasidan eng yaxshisini tanlash.
        """
        if not candidate_tools:
            return ToolSelectionResult(
                tool=None,
                score=0.0,
                explanation=f"'{required_capability}' qobiliyati uchun hech qanday asbob topilmadi.",
                required_capability=required_capability,
                candidate_tools=[]
            )

        candidate_params = candidate_params or {}
        scored_candidates: List[Tuple[ToolContract2, float, Dict[str, float], str]] = []

        for tool in candidate_tools:
            score, breakdown, why = SmartToolSelector._score_candidate(
                tool=tool,
                required_capability=required_capability,
                context=context,
                params=candidate_params,
                prefer_low_risk=prefer_low_risk
            )
            # Faqat nol bo'lmagan (mavjud bo'lgan) asboblarni hisobga olamiz
            scored_candidates.append((tool, score, breakdown, why))

        # Ballar bo'yicha kamayish tartibida saralash
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        # 1-o'rindagi asbob
        best_tool, best_score, best_breakdown, best_why = scored_candidates[0]

        # Agar eng yaxshi asbob ham butunlay yaroqsiz bo'lsa (0.0 ball)
        if best_score <= 0.0:
            return ToolSelectionResult(
                tool=None,
                score=0.0,
                explanation=f"Mavjud asboblarning barchasi ishga yaroqsiz yoki o'chirilgan holatda: {best_why}",
                required_capability=required_capability,
                candidate_tools=[t.name for t in candidate_tools],
                scoring_breakdown=best_breakdown
            )

        # Zaxira (Fallback) asbobni aniqlash
        fallback_tool: Optional[ToolContract2] = None
        for cand, c_score, _, _ in scored_candidates[1:]:
            if cand.health in (ToolHealth.AVAILABLE, ToolHealth.DEGRADED) and c_score > 0.3:
                fallback_tool = cand
                break

        explanation = (
            f"'{best_tool.name}' tanlandi (ball: {round(best_score, 2)}). "
            f"Sabab: {best_why}"
        )

        return ToolSelectionResult(
            tool=best_tool,
            score=best_score,
            explanation=explanation,
            required_capability=required_capability,
            candidate_tools=[t.name for t in candidate_tools],
            fallback_tool=fallback_tool,
            scoring_breakdown=best_breakdown
        )

    @staticmethod
    def _score_candidate(
        tool: ToolContract2,
        required_capability: str,
        context: Optional[Any],
        params: Dict[str, Any],
        prefer_low_risk: bool
    ) -> Tuple[float, Dict[str, float], str]:
        """Bitta nomzod asbobni ko'p omilli baholash"""
        breakdown: Dict[str, float] = {}
        reasons: List[str] = []

        # 1. Salomatlik va mavjudlik omili (Health Factor)
        if tool.health == ToolHealth.DISABLED:
            return 0.0, {"health": 0.0}, f"'{tool.name}' ma'muriy tarzda o'chirilgan (DISABLED)"
        elif tool.health == ToolHealth.UNAVAILABLE:
            return 0.0, {"health": 0.0}, f"'{tool.name}' xizmati hozir mavjud emas (UNAVAILABLE)"
        elif tool.health == ToolHealth.DEGRADED:
            health_score = 0.5
            reasons.append("ish faoliyati susaygan (DEGRADED)")
        else:
            health_score = 1.0
        breakdown["health"] = health_score

        # 2. Qobiliyat mosligi (Capability Match Factor)
        cap_clean = required_capability.lower().strip()
        tool_caps = [c.lower().strip() for c in tool.capabilities]

        if cap_clean in tool_caps:
            cap_score = 1.0
            reasons.append(f"qobiliyatga to'liq mos keladi ('{cap_clean}')")
        elif any(cap_clean in tc or tc in cap_clean for tc in tool_caps):
            cap_score = 0.75
            reasons.append("qobiliyatga qisman mos")
        else:
            cap_score = 0.3
        breakdown["capability_match"] = cap_score

        # 3. Parametrlar mosligi (Parameter Compatibility Factor)
        declared_keys = set(tool.parameters.keys()) if tool.parameters else set()
        required_keys = set(tool.required_parameters or [])
        supplied_keys = set(params.keys()) if params else set()

        if not required_keys and not declared_keys:
            param_score = 1.0
        else:
            # Barcha majburiy parametrlar berilganmi?
            if required_keys.issubset(supplied_keys):
                param_score = 1.0
                reasons.append("barcha majburiy parametrlar mavjud")
            else:
                missing = required_keys - supplied_keys
                # Agar parametrlar hali to'liq berilmagan bo'lsa ham, keyinchalik kiritilishi mumkin
                param_score = max(0.4, 1.0 - (len(missing) * 0.2))

            # Noma'lum parametrlar bormi?
            extra_keys = supplied_keys - declared_keys
            if extra_keys:
                param_score = max(0.2, param_score - (len(extra_keys) * 0.15))

        breakdown["parameters"] = param_score

        # 4. Xavf darajasi (Risk Level Preference)
        if prefer_low_risk:
            if tool.risk_level == RiskLevel.LOW:
                risk_score = 1.0
            elif tool.risk_level == RiskLevel.MEDIUM:
                risk_score = 0.8
            else:
                risk_score = 0.5
                reasons.append("yuqori xavfli vosita (HIGH risk)")
        else:
            risk_score = 1.0
        breakdown["risk"] = risk_score

        # 5. Ishonchlilik va oldingi muvaffaqiyatlar (Reliability Factor)
        total_runs = tool.success_count + tool.failure_count
        if total_runs > 0:
            success_rate = tool.success_count / total_runs
            reliability_score = 0.7 + (0.3 * success_rate)
        else:
            reliability_score = 0.9  # Yangi vosita uchun standart ishonch
        breakdown["reliability"] = reliability_score

        # 6. TaskContext yaqinligi (Task Context Affinity)
        context_score = 1.0
        if context:
            try:
                # Agar ushbu asbob joriy vazifada ilgari muvaffaqiyatli ishlatilgan bo'lsa
                history = getattr(context, "action_history", [])
                if any(getattr(h, "action", "") == tool.name for h in history):
                    context_score = 1.15
                    reasons.append("joriy vazifada muvaffaqiyatli ishlatilgan")
            except Exception:
                pass
        breakdown["context_affinity"] = context_score

        # Umumiy og'irlik hisobi
        # health (30%), capability (35%), parameters (15%), risk (10%), reliability (10%) * context_score
        total_score = (
            (health_score * 0.30) +
            (cap_score * 0.35) +
            (param_score * 0.15) +
            (risk_score * 0.10) +
            (reliability_score * 0.10)
        ) * context_score

        why_summary = "; ".join(reasons) if reasons else "standart ko'rsatkichlar mos"
        return total_score, breakdown, why_summary

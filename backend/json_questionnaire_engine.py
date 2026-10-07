import os
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from backend.models import QuestionItem, QuestionOption, AnswerItem, ProjectSession, DiscoveryConfidence, DimensionScore

TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ai_brd_questionnaire_template.json")

class JSONQuestionnaireEngine:
    """
    Dynamic questionnaire and scoring engine powered directly by ai_brd_questionnaire_template.json.
    
    Evaluates:
    - chatbot_instructions and workflow sequencing
    - section.applies_when conditional logic
    - question.depends_on conditional logic
    - cloud_scope filtering (AWS, Azure, GCP, IBM Cloud, ALL)
    - answer_type formatting & validation
    - confidence_model scoring formula (required weight 3, optional weight 1)
    """

    _cached_template: Optional[Dict[str, Any]] = None

    @classmethod
    def get_template(cls) -> Dict[str, Any]:
        if cls._cached_template is None:
            if os.path.exists(TEMPLATE_PATH):
                try:
                    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
                        cls._cached_template = json.load(f)
                except Exception as e:
                    print(f"Error loading {TEMPLATE_PATH}: {e}")
                    cls._cached_template = {}
            else:
                cls._cached_template = {}
        return cls._cached_template

    @classmethod
    def get_chatbot_instructions(cls) -> Dict[str, Any]:
        tpl = cls.get_template()
        return tpl.get("chatbot_instructions", {})

    @classmethod
    def get_confidence_model(cls) -> Dict[str, Any]:
        tpl = cls.get_template()
        return tpl.get("confidence_model", {})

    @classmethod
    def get_all_sections(cls) -> List[Dict[str, Any]]:
        tpl = cls.get_template()
        return tpl.get("questionnaire", {}).get("sections", [])

    @classmethod
    def get_selected_cloud(cls, answers: Dict[str, Any]) -> str:
        # Check S19.cloud_provider or q_cloud
        val = ""
        if "S19.cloud_provider" in answers:
            a = answers["S19.cloud_provider"]
            val = a.answer if hasattr(a, "answer") else str(a)
        elif "q_cloud" in answers:
            a = answers["q_cloud"]
            val = a.answer if hasattr(a, "answer") else str(a)
            
        val_lower = str(val).lower()
        if "azure" in val_lower or "microsoft" in val_lower:
            return "Azure"
        elif "aws" in val_lower or "amazon" in val_lower:
            return "AWS"
        elif "gcp" in val_lower or "google" in val_lower:
            return "GCP"
        elif "ibm" in val_lower or "watson" in val_lower:
            return "IBM Cloud"
        return "Azure"  # Default reference cloud

    @classmethod
    def evaluate_condition(cls, condition: Optional[Dict[str, Any]], answers: Dict[str, Any]) -> bool:
        if not condition:
            return True
        if condition.get("always") is True:
            return True

        if "any" in condition:
            sub_conds = condition["any"]
            return any(cls.evaluate_condition(sc, answers) for sc in sub_conds)
        if "all" in condition:
            sub_conds = condition["all"]
            return all(cls.evaluate_condition(sc, answers) for sc in sub_conds)

        q_id = condition.get("question_id")
        if not q_id:
            return True

        # Check answers store for this question
        raw_ans = None
        if q_id in answers:
            ans_obj = answers[q_id]
            raw_ans = ans_obj.answer if hasattr(ans_obj, "answer") else str(ans_obj)
        elif q_id == "S05.ai_project_types" and "q_legal_categories" in answers:
            ans_obj = answers["q_legal_categories"]
            raw_ans = ans_obj.answer if hasattr(ans_obj, "answer") else str(ans_obj)
        elif q_id == "S19.cloud_provider" and "q_cloud" in answers:
            ans_obj = answers["q_cloud"]
            raw_ans = ans_obj.answer if hasattr(ans_obj, "answer") else str(ans_obj)

        if raw_ans is None:
            return False

        op = condition.get("operator", "equals")
        expected_values = condition.get("values", [])
        if not expected_values and "value" in condition:
            expected_values = [condition["value"]]

        str_ans = str(raw_ans).lower()
        if op == "equals":
            return any(str(ev).lower() == str_ans for ev in expected_values)
        elif op == "includes_any":
            return any(str(ev).lower() in str_ans for ev in expected_values)
        elif op == "not_equals":
            return not any(str(ev).lower() == str_ans for ev in expected_values)
        elif op == "not_includes":
            return not any(str(ev).lower() in str_ans for ev in expected_values)
        return True

    @classmethod
    def is_section_applicable(cls, section: Dict[str, Any], answers: Dict[str, Any]) -> bool:
        selected_cloud = cls.get_selected_cloud(answers)
        cloud_scope = section.get("cloud_scope", ["ALL"])
        
        # Cloud scope check
        if "ALL" not in cloud_scope and selected_cloud not in cloud_scope:
            return False

        # applies_when check
        applies_when = section.get("applies_when")
        if applies_when and not cls.evaluate_condition(applies_when, answers):
            return False

        return True

    @classmethod
    def is_question_applicable(cls, question: Dict[str, Any], section: Dict[str, Any], answers: Dict[str, Any]) -> bool:
        if not cls.is_section_applicable(section, answers):
            return False

        depends_on = question.get("depends_on")
        if depends_on and not cls.evaluate_condition(depends_on, answers):
            return False

        return True

    @classmethod
    def get_applicable_questions(cls, answers: Dict[str, Any]) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """
        Returns all currently active (section, question) pairs from the JSON template.
        """
        applicable: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
        for sec in cls.get_all_sections():
            if not cls.is_section_applicable(sec, answers):
                continue
            for q in sec.get("questions", []):
                if cls.is_question_applicable(q, sec, answers):
                    applicable.append((sec, q))
        return applicable

    @classmethod
    def json_question_to_model(cls, section: Dict[str, Any], q: Dict[str, Any]) -> QuestionItem:
        q_id = q.get("id", f"{section.get('section_id')}.{q.get('key')}")
        title = f"{section.get('title')}: {q.get('key').replace('_', ' ').title()}"
        prompt = q.get("question", "")
        ans_type = q.get("answer_type", "text")
        
        # Map answer_type
        model_type = "text"
        if ans_type in ["single_select", "boolean"]:
            model_type = "dropdown"
        elif ans_type in ["multi_select", "list"]:
            model_type = "dropdown"
        elif ans_type == "number":
            model_type = "number"
        elif ans_type == "table":
            model_type = "text"

        options: List[QuestionOption] = []
        raw_options = q.get("options", [])
        if raw_options:
            for opt in raw_options:
                if isinstance(opt, dict):
                    options.append(QuestionOption(
                        value=str(opt.get("value", "")),
                        label=str(opt.get("label", opt.get("value", ""))),
                        description=opt.get("description") or opt.get("help_text")
                    ))
                else:
                    options.append(QuestionOption(
                        value=str(opt),
                        label=str(opt),
                        description=None
                    ))
        elif ans_type == "boolean":
            options = [
                QuestionOption(value="Yes", label="Yes", description="Feature is enabled / required"),
                QuestionOption(value="No", label="No", description="Not required / out of scope")
            ]

        default_val = str(q.get("example", "") or (options[0].value if options else "Standard enterprise requirement"))
        help_text = q.get("help_text") or q.get("example") or f"Section {section.get('section_id')}: {section.get('description')}"
        priority = "Blocker" if q.get("required") and section.get("section_id") in ["S01", "S02", "S03", "S05", "S19"] else ("High" if q.get("required") else "Medium")
        category = section.get("title", "Technical Architecture")

        return QuestionItem(
            id=q_id,
            title=title,
            prompt=prompt,
            type=model_type,
            options=options,
            default_value=default_val,
            category=category,
            priority=priority,
            help_text=help_text,
            why_it_matters=section.get("description", "")
        )

    @classmethod
    def calculate_template_confidence(cls, answers: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implements the exact confidence_model formula from ai_brd_questionnaire_template.json:
        confidence_percent = 100 * sum(weight * quality_score) / sum(weight) over applicable questions.
        """
        model_cfg = cls.get_confidence_model()
        weights_cfg = model_cfg.get("weights", {"required": 3, "optional": 1})
        quality_scores_cfg = model_cfg.get("answer_quality_scores", {
            "specific": 1.0,
            "vague": 0.5,
            "assumed": 0.4,
            "needs_followup": 0.25,
            "unanswered": 0.0
        })

        applicable_pairs = cls.get_applicable_questions(answers)
        total_possible_weight = 0.0
        earned_score = 0.0
        answered_count = 0
        total_applicable = len(applicable_pairs)

        section_scores: Dict[str, Dict[str, Any]] = {}

        for sec, q in applicable_pairs:
            sec_id = sec.get("section_id")
            if sec_id not in section_scores:
                section_scores[sec_id] = {
                    "title": sec.get("title"),
                    "total": 0,
                    "answered": 0,
                    "earned": 0.0,
                    "possible": 0.0
                }

            is_req = q.get("required", False)
            w = weights_cfg.get("required" if is_req else "optional", 3 if is_req else 1)
            total_possible_weight += w
            section_scores[sec_id]["possible"] += w
            section_scores[sec_id]["total"] += 1

            q_id = q.get("id", f"{sec.get('section_id')}.{q.get('key')}")
            
            # Check if answered
            ans_item = None
            if q_id in answers:
                ans_item = answers[q_id]
            else:
                # Check alias mapping
                alias_map = {
                    "S01.project_name": "q_client",
                    "S01.organization": "q_client",
                    "S02.problem_statement": "q_problem",
                    "S03.in_scope": "q_legal_categories",
                    "S19.cloud_provider": "q_cloud",
                    "S05.ai_project_types": "q_legal_categories"
                }
                alias = alias_map.get(q_id)
                if alias and alias in answers:
                    ans_item = answers[alias]

            if ans_item:
                answered_count += 1
                section_scores[sec_id]["answered"] += 1
                
                # Determine quality score
                ans_str = str(ans_item.answer if hasattr(ans_item, "answer") else ans_item)
                if len(ans_str.split()) >= 6:
                    q_score = quality_scores_cfg.get("specific", 1.0)
                elif len(ans_str.split()) >= 2:
                    q_score = quality_scores_cfg.get("assumed", 0.8)
                else:
                    q_score = quality_scores_cfg.get("vague", 0.5)

                earned_score += (w * q_score)
                section_scores[sec_id]["earned"] += (w * q_score)

        conf_pct = round(100.0 * (earned_score / max(1.0, total_possible_weight)), 1)
        
        # Band classification
        band = "Incomplete - not ready"
        for b in model_cfg.get("bands", []):
            if conf_pct >= b.get("min", 0):
                band = b.get("label", band)
                break

        return {
            "score": conf_pct,
            "band": band,
            "total_applicable_questions": total_applicable,
            "answered_questions": answered_count,
            "total_weight": total_possible_weight,
            "earned_weight": earned_score,
            "section_breakdown": section_scores,
            "selected_cloud": cls.get_selected_cloud(answers)
        }

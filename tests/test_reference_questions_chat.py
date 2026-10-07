import os
import sys
import pytest

workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

from backend.models import ProjectSession, AnswerItem, QuestionItem
from backend.agent_discovery import (
    process_user_answer, get_discovery_questions, get_all_reference_doc_questions,
    REFERENCE_DOC_QUESTIONS_52, evaluate_domain_completeness
)

def test_all_52_reference_doc_questions_loaded():
    """Verify all 52 reference document clarification questions (Q001-Q052) are loaded with full fidelity."""
    ref_qs = get_all_reference_doc_questions()
    assert len(ref_qs) == 52, f"Expected 52 reference document questions, found {len(ref_qs)}"
    
    q_ids = [q.id.replace("q_", "") for q in ref_qs]
    assert "Q001" in q_ids
    assert "Q013" in q_ids
    assert "Q044" in q_ids
    assert "Q045" in q_ids
    assert "Q052" in q_ids

    # Verify key metadata properties exist on questions
    q001 = next(q for q in ref_qs if "Q001" in q.id)
    assert q001.priority == "Blocker"
    assert q001.category == "Key Decision"
    assert "cloud platform" in q001.prompt.lower()

    q044 = next(q for q in ref_qs if "Q044" in q.id)
    assert q044.priority == "Blocker"
    assert "decision gate" in q044.prompt.lower()

    q045 = next(q for q in ref_qs if "Q045" in q.id)
    assert q045.priority == "Blocker"
    assert "expert" in q045.prompt.lower()

    q052 = next(q for q in ref_qs if "Q052" in q.id)
    assert q052.priority == "Blocker"
    assert "approvals" in q052.prompt.lower()

def test_chatbot_reference_questions_query():
    """Test that when user asks for all questions mentioned in the reference document, the chatbot returns the full 52-question breakdown."""
    session = ProjectSession(session_id="test-ref-doc-chat")
    
    user_query = "update our chatbot to ask all the possible questions mentioned in reference document to get more details about project"
    msg, is_done = process_user_answer(session, user_query)
    
    assert not is_done
    assert "Reference Document Clarification Questionnaire" in msg.content
    assert "Q001–Q052 Activated" in msg.content
    assert "Key Decision Gates & Cloud Boundaries" in msg.content
    assert "Functional Scope & Document Intelligence" in msg.content
    assert "Non-Functional Requirements, Security & Compliance" in msg.content
    assert "Operations, FinOps BoM & Phase 2 Roadmap" in msg.content
    assert msg.question_context is not None

def test_answering_reference_doc_questions():
    """Test answering granular reference document questions updates session state and domain completeness."""
    session = ProjectSession(session_id="test-answering-ref-qs")
    
    # User provides key SPOCs and constraints from reference document
    user_input = (
        "Client is PVR INOX for Contract Intelligence Platform. Delivery tier is PoC for 6.0 weeks. "
        "Azure is the only approved cloud with dedicated non-production subscription. "
        "We will provide 100 samples for each category across 6 categories. "
        "Nithin Arora is the executive sponsor, Jitender Verma is the SME SPOC, and Gaurav is the governance SPOC."
    )
    msg, is_done = process_user_answer(session, user_input)
    
    assert "q_client" in session.answers
    assert "q_tier" in session.answers
    assert "q_duration" in session.answers
    assert "q_Q044" in session.answers or "Q044" in session.answers
    assert "q_Q045" in session.answers or "Q045" in session.answers
    assert "q_Q052" in session.answers or "Q052" in session.answers
    assert "q_Q014" in session.answers or "Q014" in session.answers

if __name__ == "__main__":
    pytest.main(["-s", __file__])

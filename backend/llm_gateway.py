import os
import json
import time
import re
from typing import Dict, Any, List, Optional, Tuple
import httpx
from pydantic import BaseModel
from backend.config import AISettings, get_settings

class LLMGateway:
    """
    Multi-Cloud AI Gateway supporting:
    - Google AI Studio / GCP Gemini / Vertex AI (via REST API)
    - Microsoft Azure OpenAI (via REST API)
    - Amazon Web Services Bedrock (via boto3 / REST)
    - OpenAI-Compatible / Custom Endpoint (via REST API)
    
    Provides real-time AI invocation, connection testing with latency measurement,
    requirement extraction, dynamic clarifying question generation, and narrative synthesis.
    """

    @classmethod
    def test_connection(cls, settings: Optional[AISettings] = None) -> Dict[str, Any]:
        """
        Tests the connection to the configured AI provider in real-time.
        Measures round-trip latency in milliseconds.
        """
        res = cls._test_connection_impl(settings)
        if "message" not in res and "error" in res:
            res["message"] = res["error"]
        elif "error" not in res and not res.get("success", False):
            res["error"] = res.get("message", "Connection failed")
        return res

    @classmethod
    def _test_connection_impl(cls, settings: Optional[AISettings] = None) -> Dict[str, Any]:
        cfg = settings or get_settings()
        provider = cfg.active_provider.lower()
        t0 = time.time()
        
        try:
            if provider in ["google", "gcp", "gemini"]:
                api_key = cfg.google_api_key.strip() if cfg.google_api_key else ""
                if not api_key:
                    return {
                        "success": False,
                        "provider": "google",
                        "error": "Google API key is missing. Please provide your Gemini API key.",
                        "latency_ms": 0
                    }
                
                model = cfg.google_model or "gemini-2.5-flash"
                base_url = (cfg.google_endpoint or "https://generativelanguage.googleapis.com").rstrip("/")
                endpoint = f"{base_url}/v1beta/models/{model}:generateContent?key={api_key}"
                
                payload = {
                    "contents": [{"parts": [{"text": "Respond with 'AI_ONLINE' to verify live connection."}]}],
                    "generationConfig": {"temperature": 0.0, "maxOutputTokens": 20}
                }
                
                with httpx.Client(timeout=15.0) as client:
                    resp = client.post(endpoint, json=payload, headers={"Content-Type": "application/json"})
                    latency = round((time.time() - t0) * 1000, 1)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        text = ""
                        try:
                            text = data["candidates"][0]["content"]["parts"][0]["text"]
                        except Exception:
                            text = "Connected"
                        return {
                            "success": True,
                            "provider": "Google AI Studio / Gemini",
                            "model": model,
                            "latency_ms": latency,
                            "message": f"Connected to {model} successfully! Latency: {latency}ms. Response: {text.strip()}"
                        }
                    else:
                        return {
                            "success": False,
                            "provider": "Google AI Studio",
                            "model": model,
                            "latency_ms": latency,
                            "error": f"HTTP {resp.status_code}: {resp.text}"
                        }

            elif provider in ["azure", "azure_openai"]:
                endpoint = (cfg.azure_endpoint or "").rstrip("/")
                api_key = cfg.azure_api_key or ""
                deployment = cfg.azure_deployment or "gpt-4o"
                api_ver = cfg.azure_api_version or "2024-06-01"
                
                if not endpoint or not api_key:
                    return {
                        "success": False,
                        "provider": "azure",
                        "error": "Azure OpenAI Endpoint or API Key is missing.",
                        "latency_ms": 0
                    }
                    
                url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_ver}"
                payload = {
                    "messages": [{"role": "user", "content": "Respond with 'AI_ONLINE' to verify connection."}],
                    "max_tokens": 20,
                    "temperature": 0.0
                }
                
                with httpx.Client(timeout=15.0) as client:
                    resp = client.post(url, json=payload, headers={"api-key": api_key, "Content-Type": "application/json"})
                    latency = round((time.time() - t0) * 1000, 1)
                    
                    if resp.status_code == 200:
                        return {
                            "success": True,
                            "provider": "Microsoft Azure OpenAI",
                            "model": deployment,
                            "latency_ms": latency,
                            "message": f"Connected to Azure OpenAI {deployment} successfully! Latency: {latency}ms."
                        }
                    else:
                        return {
                            "success": False,
                            "provider": "Azure OpenAI",
                            "model": deployment,
                            "latency_ms": latency,
                            "error": f"HTTP {resp.status_code}: {resp.text}"
                        }

            elif provider in ["aws", "bedrock"]:
                region = cfg.aws_region or "us-east-1"
                model_id = cfg.aws_model_id or "anthropic.claude-3-5-sonnet-20240620-v1:0"
                access_key = cfg.aws_access_key_id or ""
                secret_key = cfg.aws_secret_access_key or ""
                
                if not access_key or not secret_key:
                    return {
                        "success": False,
                        "provider": "aws",
                        "error": "AWS Access Key ID or Secret Access Key is missing.",
                        "latency_ms": 0
                    }
                
                try:
                    import boto3
                    client_kwargs = {
                        "service_name": "bedrock-runtime",
                        "region_name": region,
                        "aws_access_key_id": access_key,
                        "aws_secret_access_key": secret_key
                    }
                    if cfg.aws_session_token:
                        client_kwargs["aws_session_token"] = cfg.aws_session_token
                        
                    client = boto3.client(**client_kwargs)
                    
                    if "claude" in model_id.lower():
                        body = json.dumps({
                            "anthropic_version": "bedrock-2023-05-31",
                            "max_tokens": 20,
                            "messages": [{"role": "user", "content": "Respond with 'AI_ONLINE'"}]
                        })
                    else:
                        body = json.dumps({"inputText": "Respond with 'AI_ONLINE'"})
                        
                    response = client.invoke_model(modelId=model_id, body=body)
                    latency = round((time.time() - t0) * 1000, 1)
                    return {
                        "success": True,
                        "provider": "AWS Bedrock",
                        "model": model_id,
                        "latency_ms": latency,
                        "message": f"Connected to AWS Bedrock {model_id} successfully! Latency: {latency}ms."
                    }
                except Exception as b_err:
                    latency = round((time.time() - t0) * 1000, 1)
                    return {
                        "success": False,
                        "provider": "AWS Bedrock",
                        "model": model_id,
                        "latency_ms": latency,
                        "error": str(b_err)
                    }

            elif provider in ["openai", "custom"]:
                endpoint = (cfg.openai_endpoint or "https://api.openai.com/v1").rstrip("/")
                api_key = cfg.openai_api_key or ""
                model = cfg.openai_model or "gpt-4o"
                
                if not api_key:
                    return {
                        "success": False,
                        "provider": "openai",
                        "error": "OpenAI / Custom API Key is missing.",
                        "latency_ms": 0
                    }
                    
                url = f"{endpoint}/chat/completions"
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": "Respond with 'AI_ONLINE'"}],
                    "max_tokens": 20,
                    "temperature": 0.0
                }
                
                with httpx.Client(timeout=15.0) as client:
                    resp = client.post(url, json=payload, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
                    latency = round((time.time() - t0) * 1000, 1)
                    if resp.status_code == 200:
                        return {
                            "success": True,
                            "provider": "OpenAI / Custom API",
                            "model": model,
                            "latency_ms": latency,
                            "message": f"Connected to {model} successfully! Latency: {latency}ms."
                        }
                    else:
                        return {
                            "success": False,
                            "provider": "OpenAI / Custom API",
                            "model": model,
                            "latency_ms": latency,
                            "error": f"HTTP {resp.status_code}: {resp.text}"
                        }
            else:
                res = {
                    "success": False,
                    "provider": provider,
                    "error": f"Unsupported provider: {provider}",
                    "latency_ms": 0
                }
                res["message"] = res["error"]
                return res

        except Exception as ex:
            res = {
                "success": False,
                "provider": provider,
                "error": f"Connection exception: {str(ex)}",
                "latency_ms": round((time.time() - t0) * 1000, 1)
            }
            res["message"] = res["error"]
            return res

    @classmethod
    def generate_text(
        cls,
        prompt: str,
        system_instruction: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.2
    ) -> Optional[str]:
        """
        Generates text using the configured cloud AI provider.
        Returns None if live invocation fails or is not configured.
        """
        cfg = get_settings()
        provider = cfg.active_provider.lower()

        try:
            if provider in ["google", "gcp", "gemini"]:
                api_key = cfg.google_api_key.strip() if cfg.google_api_key else ""
                if not api_key:
                    return None
                model = cfg.google_model or "gemini-2.5-flash"
                base_url = (cfg.google_endpoint or "https://generativelanguage.googleapis.com").rstrip("/")
                endpoint = f"{base_url}/v1beta/models/{model}:generateContent?key={api_key}"
                
                contents = [{"parts": [{"text": prompt}]}]
                payload = {
                    "contents": contents,
                    "generationConfig": {
                        "temperature": temperature,
                        "maxOutputTokens": max_tokens
                    }
                }
                if system_instruction:
                    payload["systemInstruction"] = {
                        "parts": [{"text": system_instruction}]
                    }
                
                with httpx.Client(timeout=5.0) as client:
                    resp = client.post(endpoint, json=payload, headers={"Content-Type": "application/json"})
                    if resp.status_code == 200:
                        data = resp.json()
                        return data["candidates"][0]["content"]["parts"][0]["text"]

            elif provider in ["azure", "azure_openai"]:
                endpoint = (cfg.azure_endpoint or "").rstrip("/")
                api_key = cfg.azure_api_key or ""
                deployment = cfg.azure_deployment or "gpt-4o"
                api_ver = cfg.azure_api_version or "2024-06-01"
                
                if not endpoint or not api_key:
                    return None
                    
                url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_ver}"
                messages = []
                if system_instruction:
                    messages.append({"role": "system", "content": system_instruction})
                messages.append({"role": "user", "content": prompt})
                
                payload = {
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
                with httpx.Client(timeout=5.0) as client:
                    resp = client.post(url, json=payload, headers={"api-key": api_key, "Content-Type": "application/json"})
                    if resp.status_code == 200:
                        data = resp.json()
                        return data["choices"][0]["message"]["content"]

            elif provider in ["aws", "bedrock"]:
                region = cfg.aws_region or "us-east-1"
                model_id = cfg.aws_model_id or "anthropic.claude-3-5-sonnet-20240620-v1:0"
                access_key = cfg.aws_access_key_id or ""
                secret_key = cfg.aws_secret_access_key or ""
                
                if not access_key or not secret_key:
                    return None
                
                import boto3
                client_kwargs = {
                    "service_name": "bedrock-runtime",
                    "region_name": region,
                    "aws_access_key_id": access_key,
                    "aws_secret_access_key": secret_key
                }
                if cfg.aws_session_token:
                    client_kwargs["aws_session_token"] = cfg.aws_session_token
                    
                client = boto3.client(**client_kwargs)
                if "claude" in model_id.lower():
                    messages = [{"role": "user", "content": prompt}]
                    body_dict = {
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "messages": messages
                    }
                    if system_instruction:
                        body_dict["system"] = system_instruction
                    response = client.invoke_model(modelId=model_id, body=json.dumps(body_dict))
                    resp_body = json.loads(response["body"].read().decode("utf-8"))
                    return resp_body["content"][0]["text"]

            elif provider in ["openai", "custom"]:
                endpoint = (cfg.openai_endpoint or "https://api.openai.com/v1").rstrip("/")
                api_key = cfg.openai_api_key or ""
                model = cfg.openai_model or "gpt-4o"
                
                if not api_key:
                    return None
                url = f"{endpoint}/chat/completions"
                messages = []
                if system_instruction:
                    messages.append({"role": "system", "content": system_instruction})
                messages.append({"role": "user", "content": prompt})
                payload = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
                with httpx.Client(timeout=5.0) as client:
                    resp = client.post(url, json=payload, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
                    if resp.status_code == 200:
                        data = resp.json()
                        return data["choices"][0]["message"]["content"]

        except Exception as e:
            print(f"[LLMGateway] Error calling provider {provider}: {e}")
            return None

        return None

    @classmethod
    def generate_json(
        cls,
        prompt: str,
        system_instruction: Optional[str] = None,
        max_tokens: int = 4000
    ) -> Optional[Dict[str, Any]]:
        """
        Prompts the active LLM to return strict JSON and parses the output.
        """
        sys_prompt = (
            (system_instruction or "") +
            "\n\nCRITICAL: Return ONLY a valid JSON object matching the requested schema. "
            "Do not include any markdown backticks, explanations, or commentary outside the JSON."
        )
        raw_text = cls.generate_text(prompt, system_instruction=sys_prompt, max_tokens=max_tokens, temperature=0.1)
        if not raw_text:
            return None
            
        clean_text = raw_text.strip()
        # Strip markdown fences if present
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        elif clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()
        
        try:
            return json.loads(clean_text)
        except Exception as e:
            # Fallback regex extraction of first {...} block
            m = re.search(r'\{.*\}', clean_text, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(0))
                except Exception:
                    pass
            print(f"[LLMGateway] JSON parsing error: {e}")
            return None

    @classmethod
    def extract_rfp_intelligence(cls, document_text: str) -> Optional[Dict[str, Any]]:
        """
        Real-time RFP / Project Intake intelligence extraction per reference.txt Section 1 & Section 4.
        Extracts Canonical Project Model items from RFP text.
        """
        system = (
            "You are an expert Enterprise Solutions Architect and AI Requirements Intelligence Agent. "
            "Analyze the client document and extract structured requirements according to the Canonical Project Model."
        )
        prompt = f"""Analyze the following client proposal, RFP, or scope document:

---
{document_text[:20000]}
---

Extract and return a JSON object with EXACTLY the following structure:
{{
  "client_name": "Name of the client organization",
  "project_title": "Descriptive title of the project/initiative",
  "domain": "Domain e.g. Contract Intelligence, Customer Support, Financial Fraud, Document Extraction, or Enterprise Search",
  "problem_statement": "2-4 sentence summary of business pain points and bottlenecks",
  "delivery_tier": "PoC | Pilot | MVP | Production Grade",
  "in_scope": ["Item 1", "Item 2", "Item 3", "Item 4"],
  "out_of_scope": ["Item 1", "Item 2", "Item 3"],
  "user_personas": [
    {{"name": "Persona 1", "role": "Role description", "pain_point": "Key pain point"}},
    {{"name": "Persona 2", "role": "Role description", "pain_point": "Key pain point"}}
  ],
  "functional_capabilities": ["Capability 1", "Capability 2", "Capability 3"],
  "non_functional_requirements": ["NFR 1 (e.g. latency)", "NFR 2 (e.g. throughput)"],
  "data_characteristics": "Description of volume, formats, and sources",
  "integrations": ["Integration 1", "Integration 2"],
  "cloud_platform": "Microsoft Azure | Google Cloud Platform | Amazon Web Services",
  "compliance_posture": "Internal policy only | Regulated Moderate | Regulated High",
  "security_posture": "Standard | High | Comprehensive",
  "estimated_weeks": 6.0,
  "named_users": 200,
  "concurrent_users": 50,
  "daily_requests": 2000
}}"""
        return cls.generate_json(prompt, system_instruction=system, max_tokens=3000)

    @classmethod
    def clarify_user_input(
        cls,
        question_title: str,
        question_prompt: str,
        user_input: str,
        current_answer: str,
        category: str
    ) -> Optional[Dict[str, Any]]:
        """
        Real-time Requirements Intelligence:
        Interprets natural language user responses, evaluates ambiguity,
        and generates targeted dynamic clarification grounded in ai_brd_questionnaire_template.json rules.
        """
        system = (
            "You are an AI Requirements Intelligence Agent conducting an enterprise AI discovery interview "
            "based on the AI Project BRD Questionnaire (AWS, Azure, GCP, IBM Cloud). "
            "Evaluate if the user's answer is sufficiently specific or if it is ambiguous/vague according to: "
            "specific = measurable/named/verifiable targets; vague = generic terms ('fast', 'good'); assumed = chatbot inferred. "
            "Never hallucinate or recommend services outside the single selected cloud platform. "
            "CRITICAL: Always ask EXACTLY ONE focused question at a time. Never dump multiple questions in a single message."
        )
        prompt = f"""Context:
Question: {question_title}
Prompt: {question_prompt}
Category: {category}
User Input: "{user_input}"

Analyze the user's input. Return a JSON object with:
{{
  "is_ambiguous": true or false,
  "confidence": 0.0 to 1.0,
  "clarification_needed": true or false,
  "reason": "Brief reason if ambiguous or clear",
  "normalized_value": "Clean, authoritative project requirement statement synthesized from input",
  "follow_up_prompt": "Targeted question to ask user if clarification_needed is true, else empty",
  "suggested_options": [
    {{"label": "Option A Title", "value": "Detailed specification of Option A"}},
    {{"label": "Option B Title", "value": "Detailed specification of Option B"}},
    {{"label": "Option C Title", "value": "Detailed specification of Option C"}}
  ]
}}"""
        return cls.generate_json(prompt, system_instruction=system, max_tokens=1500)

    @classmethod
    def interview_discovery_agent(
        cls,
        current_section: Dict[str, Any],
        current_question: Dict[str, Any],
        user_message: str,
        session_answers: Dict[str, Any],
        accumulated_requirements: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Conducts discovery interview turns directly powered by ai_brd_questionnaire_template.json rules.
        """
        system = (
            "You are an expert Enterprise AI Business Analyst & Solutions Architect interviewing a client. "
            "Your interview is strictly guided by the AI Project BRD Questionnaire Template (AWS, Azure, GCP, IBM Cloud). "
            "Rules:\n"
            "1. Ask S01 (Project/Client), S02 (Problem/Objectives), S03 (Scope), S05 (Project Types), and S19 (Cloud Provider) first.\n"
            "2. Never recommend or mention services from non-selected clouds.\n"
            "3. Challenge vague answers for measurable metrics.\n"
            "4. Acknowledge user requirements conversationally, check if they have more, and summarize clearly.\n"
            "5. Return atomic, verifiable requirements."
        )
        prompt = f"""Active Section: {current_section.get('section_id')} - {current_section.get('title')}
Question ID: {current_question.get('id')} ({current_question.get('key')})
Question Text: {current_question.get('question')}
Help Text: {current_question.get('help_text', '')}

User Input: "{user_message}"
Previously Accumulated Requirements: {json.dumps(accumulated_requirements or [])}
Active Answers: {json.dumps({k: (v.answer if hasattr(v, 'answer') else str(v)) for k, v in list(session_answers.items())[-8:]})}

Generate a JSON response:
{{
  "acknowledgment": "Conversational acknowledgment of what was entered",
  "is_end_of_requirements": true or false,
  "extracted_requirements": ["Requirement 1", "Requirement 2"],
  "next_prompt": "What to ask next or follow up with",
  "suggested_options": [
    {{"label": "Option Label", "value": "Option Value"}}
  ]
}}"""
        return cls.generate_json(prompt, system_instruction=system, max_tokens=1500)

    @classmethod
    def synthesize_narratives(
        cls,
        client_name: str,
        project_title: str,
        problem_statement: str,
        delivery_tier: str,
        cloud_platform: str,
        scope_in: List[str],
        scope_out: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Real-time Solution Intelligence:
        Synthesizes executive summary, 6-sentence solution summary,
        target architecture narrative, and data flow narrative tailored to the exact client.
        """
        system = (
            "You are a Principal Enterprise Solutions Architect creating a formal Business Requirements Document (BRD). "
            "Write precise, authoritative, professional narratives strictly grounded in the inputs without generic fluff."
        )
        prompt = f"""Project Context:
- Client: {client_name}
- Initiative: {project_title}
- Delivery Tier: {delivery_tier}
- Cloud Platform: {cloud_platform}
- Problem Statement: {problem_statement}
- In-Scope Capabilities: {', '.join(scope_in[:8])}
- Out-of-Scope Demarcations: {', '.join(scope_out[:6])}

Generate a JSON object with:
{{
  "executive_summary": "Comprehensive 3-paragraph executive summary detailing strategic context, business challenges, proposed AI architecture, and tangible ROI.",
  "solution_summary_six_sentences": "Exactly 6 clear, concise sentences summarizing the end-to-end technical approach.",
  "target_architecture_narrative": "Detailed 2-3 paragraph technical architecture narrative explaining the ingestion layer, AI orchestration, vector/data persistence, presentation, security, and cloud services on {cloud_platform}.",
  "data_flow_narrative": "Detailed sequential end-to-end data flow narrative tracing data from ingestion through preprocessing, embedding, reasoning, business evaluation, and persistence."
}}"""
        return cls.generate_json(prompt, system_instruction=system, max_tokens=3500)

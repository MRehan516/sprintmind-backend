import json
import logging
import time
from typing import List
from datetime import datetime
from ibm_watsonx_ai.foundation_models import Model
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

from app.config import settings
from app.schemas import (
    AnalyzeRequest,
    SignalItem,
    FeatureRecommendation,
    Challenge,
    AnalysisOutput
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_watsonx_model() -> Model:
    """Initialize and return WatsonX model instance."""
    model_id = "ibm/granite-13b-chat-v2"
    
    parameters = {
        GenParams.DECODING_METHOD: "greedy",
        GenParams.MAX_NEW_TOKENS: 2000,
        GenParams.TEMPERATURE: 0.7,
        GenParams.TOP_P: 1,
        GenParams.TOP_K: 50
    }
    
    model = Model(
        model_id=model_id,
        params=parameters,
        credentials={
            "apikey": settings.watsonx_api_key,
            "url": settings.watsonx_url
        },
        project_id=settings.watsonx_project_id
    )
    
    return model


def extract_signals(interviews: str, jira: str, analytics: str) -> List[SignalItem]:
    """
    Extract user signals from product management inputs.
    
    Args:
        interviews: User interview transcripts
        jira: Jira backlog items
        analytics: Analytics data observations
        
    Returns:
        List of SignalItem objects
    """
    system_prompt = (
        "SYSTEM INSTRUCTION: You are a senior product manager analyzing user research. You MUST extract meaningful signals from the data. Do NOT return empty lists.\n\n"
        "CRITICAL REQUIREMENTS:\n"
        "1. You MUST return valid JSON - no markdown, no code blocks, no explanations\n"
        "2. The response MUST be a JSON array with at least 5 signal objects\n"
        "3. Each object MUST have ALL these fields:\n"
        "   - type: must be exactly 'pain', 'request', or 'behavior'\n"
        "   - description: string (one clear sentence)\n"
        "   - source: must be exactly 'interviews', 'jira', or 'analytics'\n"
        "   - intensity: integer between 1-5 (5 = most severe/important)\n\n"
        "4. Do NOT return empty arrays []\n"
        "5. Start your response with [ and end with ]\n"
        "6. Extract EVERY distinct pain point, feature request, and behavior pattern\n\n"
        "Analyze the following product management inputs and extract user signals:"
    )
    
    user_message = f"""# INTERVIEWS
{interviews}

# JIRA BACKLOG
{jira}

# ANALYTICS DATA
{analytics}"""
    
    try:
        model = _get_watsonx_model()
        
        # First attempt
        prompt = f"{system_prompt}\n\n{user_message}"
        response = model.generate_text(prompt=prompt)
        
        # Try to parse JSON
        try:
            # Extract JSON array from response
            response_text = response.strip()
            # Find JSON array boundaries
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_text = response_text[start_idx:end_idx]
                signals_data = json.loads(json_text)
                
                # Validate and convert to SignalItem objects
                signals = []
                for item in signals_data:
                    try:
                        signal = SignalItem(**item)
                        signals.append(signal)
                    except Exception as e:
                        logger.warning(f"Invalid signal item: {item}, error: {e}")
                        continue
                
                logger.info(f"Successfully extracted {len(signals)} signals")
                return signals
            else:
                raise ValueError("No JSON array found in response")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"First attempt failed to parse JSON: {e}. Retrying with simplified prompt.")
            
            # Second attempt with simplified prompt
            simplified_prompt = (
                "Extract user signals as JSON array. Each item needs: type, description, source, intensity. "
                f"\n\n{user_message}"
            )
            response = model.generate_text(prompt=simplified_prompt)
            
            try:
                response_text = response.strip()
                start_idx = response_text.find('[')
                end_idx = response_text.rfind(']') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_text = response_text[start_idx:end_idx]
                    signals_data = json.loads(json_text)
                    
                    signals = []
                    for item in signals_data:
                        try:
                            signal = SignalItem(**item)
                            signals.append(signal)
                        except Exception as e:
                            logger.warning(f"Invalid signal item: {item}, error: {e}")
                            continue
                    
                    logger.info(f"Successfully extracted {len(signals)} signals on retry")
                    return signals
                else:
                    raise ValueError("No JSON array found in retry response")
                    
            except Exception as e:
                logger.error(f"Second attempt also failed: {e}")
                return []
                
    except Exception as e:
        logger.error(f"Error in extract_signals: {e}")
        return []


def rank_features(signals: List[SignalItem]) -> List[FeatureRecommendation]:
    """
    Rank and recommend top features based on signals.
    
    Args:
        signals: List of extracted signals
        
    Returns:
        List of top 3 FeatureRecommendation objects
    """
    system_prompt = (
        "SYSTEM INSTRUCTION: You are a senior product manager. You MUST analyze the provided data and output exactly three high-priority features. Do NOT return empty lists.\n\n"
        "CRITICAL REQUIREMENTS:\n"
        "1. You MUST return valid JSON - no markdown, no code blocks, no explanations\n"
        "2. The response MUST be a JSON array with EXACTLY 3 feature objects\n"
        "3. Each object MUST have ALL these fields:\n"
        "   - feature_name: string (clear, actionable feature name)\n"
        "   - problem_it_solves: string (specific user problem)\n"
        "   - supporting_evidence: array of strings (minimum 2 evidence points)\n"
        "   - priority_score: integer between 1-100 (higher = more important)\n"
        "   - estimated_user_impact: string (one sentence describing impact)\n\n"
        "4. Do NOT return empty arrays []\n"
        "5. Start your response with [ and end with ]\n"
        "6. If signals are limited, synthesize features from available data\n\n"
        "Given these product signals, identify exactly the top 3 features to build next:"
    )
    
    # Convert signals to JSON for the prompt
    signals_json = json.dumps([signal.model_dump() for signal in signals], indent=2)
    user_message = f"Product signals:\n{signals_json}"
    
    try:
        model = _get_watsonx_model()
        
        # First attempt
        prompt = f"{system_prompt}\n\n{user_message}"
        response = model.generate_text(prompt=prompt)
        
        try:
            # Extract JSON array from response
            response_text = response.strip()
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_text = response_text[start_idx:end_idx]
                features_data = json.loads(json_text)
                
                # Validate and convert to FeatureRecommendation objects
                features = []
                for item in features_data[:3]:  # Ensure only top 3
                    try:
                        feature = FeatureRecommendation(**item)
                        features.append(feature)
                    except Exception as e:
                        logger.warning(f"Invalid feature item: {item}, error: {e}")
                        continue
                
                logger.info(f"Successfully ranked {len(features)} features")
                return features
            else:
                raise ValueError("No JSON array found in response")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"First attempt failed to parse JSON: {e}. Retrying with simplified prompt.")
            
            # Second attempt with simplified prompt
            simplified_prompt = (
                "Identify top 3 features as JSON array. Each needs: feature_name, problem_it_solves, "
                "supporting_evidence (array), priority_score (1-100), estimated_user_impact. "
                f"\n\n{user_message}"
            )
            response = model.generate_text(prompt=simplified_prompt)
            
            try:
                response_text = response.strip()
                start_idx = response_text.find('[')
                end_idx = response_text.rfind(']') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_text = response_text[start_idx:end_idx]
                    features_data = json.loads(json_text)
                    
                    features = []
                    for item in features_data[:3]:
                        try:
                            feature = FeatureRecommendation(**item)
                            features.append(feature)
                        except Exception as e:
                            logger.warning(f"Invalid feature item: {item}, error: {e}")
                            continue
                    
                    logger.info(f"Successfully ranked {len(features)} features on retry")
                    return features
                else:
                    raise ValueError("No JSON array found in retry response")
                    
            except Exception as e:
                logger.error(f"Second attempt also failed: {e}")
                return []
                
    except Exception as e:
        logger.error(f"Error in rank_features: {e}")
        return []


def generate_challenges(features: List[FeatureRecommendation]) -> List[Challenge]:
    """
    Generate challenges for each recommended feature.
    
    Args:
        features: List of recommended features
        
    Returns:
        List of Challenge objects
    """
    system_prompt = (
        "SYSTEM INSTRUCTION: You are a senior product manager identifying risks. You MUST generate challenges for each feature. Do NOT return empty lists.\n\n"
        "CRITICAL REQUIREMENTS:\n"
        "1. You MUST return valid JSON - no markdown, no code blocks, no explanations\n"
        "2. The response MUST be a JSON array with one object per feature\n"
        "3. Each object MUST have ALL these fields:\n"
        "   - feature_name: string (must match the input feature name exactly)\n"
        "   - challenges: array of exactly 2 strings (specific concerns)\n\n"
        "4. Do NOT return empty arrays []\n"
        "5. Start your response with [ and end with ]\n"
        "6. Be specific about implementation complexity, market timing, user behavior, or evidence gaps\n\n"
        "For each recommended feature, generate exactly 2 specific reasons why it might be the WRONG priority right now:"
    )
    
    # Convert features to JSON for the prompt
    features_json = json.dumps([feature.model_dump() for feature in features], indent=2)
    user_message = f"Recommended features:\n{features_json}"
    
    try:
        model = _get_watsonx_model()
        
        # First attempt
        prompt = f"{system_prompt}\n\n{user_message}"
        response = model.generate_text(prompt=prompt)
        
        try:
            # Extract JSON array from response
            response_text = response.strip()
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_text = response_text[start_idx:end_idx]
                challenges_data = json.loads(json_text)
                
                # Validate and convert to Challenge objects
                challenges = []
                for item in challenges_data:
                    try:
                        challenge = Challenge(**item)
                        challenges.append(challenge)
                    except Exception as e:
                        logger.warning(f"Invalid challenge item: {item}, error: {e}")
                        continue
                
                logger.info(f"Successfully generated challenges for {len(challenges)} features")
                return challenges
            else:
                raise ValueError("No JSON array found in response")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"First attempt failed to parse JSON: {e}. Retrying with simplified prompt.")
            
            # Second attempt with simplified prompt
            simplified_prompt = (
                "For each feature, list 2 reasons it might be wrong priority. "
                "Return JSON array with feature_name and challenges (array of 2 strings). "
                f"\n\n{user_message}"
            )
            response = model.generate_text(prompt=simplified_prompt)
            
            try:
                response_text = response.strip()
                start_idx = response_text.find('[')
                end_idx = response_text.rfind(']') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_text = response_text[start_idx:end_idx]
                    challenges_data = json.loads(json_text)
                    
                    challenges = []
                    for item in challenges_data:
                        try:
                            challenge = Challenge(**item)
                            challenges.append(challenge)
                        except Exception as e:
                            logger.warning(f"Invalid challenge item: {item}, error: {e}")
                            continue
                    
                    logger.info(f"Successfully generated challenges for {len(challenges)} features on retry")
                    return challenges
                else:
                    raise ValueError("No JSON array found in retry response")
                    
            except Exception as e:
                logger.error(f"Second attempt also failed: {e}")
                return []
                
    except Exception as e:
        logger.error(f"Error in generate_challenges: {e}")
        return []


def run_consensus_pipeline(request: AnalyzeRequest) -> AnalysisOutput:
    """
    Orchestrate the complete analysis pipeline.
    
    Args:
        request: AnalyzeRequest with user inputs
        
    Returns:
        AnalysisOutput with complete analysis results
    """
    start_time = time.perf_counter()
    
    # Step 1: Extract signals
    logger.info("Step 1: Extracting signals...")
    signals = extract_signals(
        interviews=request.interviews,
        jira=request.jira_backlog,
        analytics=request.analytics_data
    )
    
    # Step 2: Rank features
    logger.info("Step 2: Ranking features...")
    features = rank_features(signals)
    
    # Step 3: Generate challenges
    logger.info("Step 3: Generating challenges...")
    challenges = generate_challenges(features)
    
    # Calculate processing time
    end_time = time.perf_counter()
    processing_time_ms = int((end_time - start_time) * 1000)
    
    # Calculate consensus score (average priority score)
    if features:
        consensus_score = sum(f.priority_score for f in features) / len(features)
    else:
        consensus_score = 0.0
    
    # Create output
    output = AnalysisOutput(
        top_features=features,
        challenges_per_feature=challenges,
        consensus_score=consensus_score,
        generated_at=datetime.utcnow(),
        processing_time_ms=processing_time_ms
    )
    
    logger.info(f"Pipeline completed in {processing_time_ms}ms with consensus score {consensus_score:.2f}")
    
    return output


# Made with Bob
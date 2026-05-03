"""
Standalone test for the LLM pipeline.
Tests run_consensus_pipeline with hardcoded sample data.
"""
import json
from app.schemas import AnalyzeRequest
from app.pipeline import run_consensus_pipeline


def main():
    """Test the pipeline with sample data."""
    
    # Sample interview notes (3 sentences)
    interviews = """
    Users mentioned they struggle to find relevant documents quickly in the current system.
    Multiple customers expressed frustration with the slow loading times on mobile devices.
    Several interviewees requested a dark mode feature for better nighttime usability.
    """
    
    # Sample Jira backlog (5 items)
    jira = """
    PROJ-101: Implement advanced search filters for document repository
    PROJ-102: Optimize mobile app performance and reduce load times
    PROJ-103: Add dark mode theme support across all platforms
    PROJ-104: Fix bug in user authentication flow causing session timeouts
    PROJ-105: Integrate third-party analytics dashboard for admin users
    """
    
    # Sample analytics observations (2 items)
    analytics = """
    Analytics show 65% of users abandon the search after the first failed attempt.
    Mobile bounce rate is 45% higher than desktop, with most exits occurring during initial load.
    """
    
    # Create request
    request = AnalyzeRequest(
        user_email="test@example.com",
        interviews=interviews,
        jira_backlog=jira,
        analytics_data=analytics
    )
    
    print("=" * 80)
    print("TESTING LLM PIPELINE")
    print("=" * 80)
    print("\nInput Data:")
    print(f"- Interviews: {len(interviews)} characters")
    print(f"- Jira Backlog: {len(jira)} characters")
    print(f"- Analytics: {len(analytics)} characters")
    print("\nRunning pipeline...\n")
    
    try:
        # Run the pipeline
        output = run_consensus_pipeline(request)
        
        # Convert to dict for pretty printing
        output_dict = output.model_dump()
        
        print("=" * 80)
        print("PIPELINE OUTPUT")
        print("=" * 80)
        print(json.dumps(output_dict, indent=2, default=str))
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"[OK] Top Features: {len(output.top_features)}")
        print(f"[OK] Challenges: {len(output.challenges_per_feature)}")
        print(f"[OK] Consensus Score: {output.consensus_score:.2f}")
        print(f"[OK] Processing Time: {output.processing_time_ms}ms")
        print(f"[OK] Generated At: {output.generated_at}")
        
        if output.top_features:
            print("\n[SUCCESS] Pipeline returned valid output!")
            return True
        else:
            print("\n[WARNING] Pipeline returned empty features (partial results)")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] Pipeline failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)


# Made with Bob
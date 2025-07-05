"""GPT-4o extraction module for Bank of America Sell Side Indicator data."""

import sys
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

from openai import OpenAI


class SSIExtractor:
    """Extract SSI values from article content using GPT-4o."""
    
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for GPT-4o."""
        return """You are a financial data extraction specialist with expertise in Bank of America research and sell-side indicators.

Your task: Extract Bank of America Sell-Side Indicator (SSI) values from complete investing.com articles.

ABOUT THE SSI:
- The SSI measures average recommended equity allocation from sell-side strategists
- Typical range: 40-80%
- It's a contrarian sentiment indicator
- Published monthly by Bank of America

CRITICAL TIMING RULE: SSI data for month N is published in month N+1. Examples:
- May 2024 SSI data appears in June 2024 articles
- December 2024 SSI data appears in January 2025 articles

EXPERTISE AREAS:
- Understanding of financial research publication timing
- Recognition of SSI vs other Bank of America indicators (like Fund Manager Survey)
- Ability to distinguish between current and historical SSI values
- Understanding of monthly vs quarterly reporting cycles

EXTRACTION GUIDELINES:
1. Read the complete article carefully
2. Look for specific phrases: "Sell-Side Indicator", "SSI", "recommended equity allocation"
3. Identify the exact percentage value (e.g., 55.7%)
4. Determine which month the SSI value refers to (not the publication month)
5. Consider the publication timing offset
6. Include supporting context from the article

Return ONLY valid JSON object with no additional text."""
    
    def _build_user_prompt(self, article: Dict[str, Any], target_months: List[str], article_text: str) -> str:
        """Build the user prompt for a specific article."""
        month_list = ", ".join(target_months)
        current_date = datetime.now().strftime("%B %d, %Y")
        
        return f"""CONTEXT: Today's date is {current_date}. You are analyzing financial articles to extract Bank of America Sell-Side Indicator (SSI) data.

Analyze this complete investing.com article for Bank of America Sell-Side Indicator (SSI) data:

ARTICLE METADATA:
Title: {article['title']}
Publication Date: {article['date']}
URL: {article['link']}
Content Length: {len(article_text)} characters

TARGET MONTHS: {month_list}

FULL ARTICLE TEXT:
{article_text}

EXTRACTION TASK:
1. Carefully read the complete article
2. Identify any Bank of America Sell-Side Indicator (SSI) values
3. Determine which specific month each SSI value refers to
4. Consider the publication timing (article published in month N+1 for month N data)
5. Extract the percentage value and provide context

Return a JSON object with this format:
{{
  "results": [
    {{
      "month": "May 2024",
      "value": 55.7,
      "confidence": "high",
      "context": "brief supporting quote from article",
      "reasoning": "why this value corresponds to this month"
    }}
  ]
}}

If no SSI values found, return {{"results": []}}.
Only include values in the 40-80% range that clearly refer to the SSI."""
    
    def _truncate_article_text(self, article_text: str, max_chars: int = 15000) -> str:
        """Truncate article text to stay within token limits."""
        if len(article_text) > max_chars:
            truncated = article_text[:max_chars] + "\n\n[TRUNCATED - Content exceeds token limit]"
            print(f"   ⚠️  Article truncated from {len(article_text)} to {max_chars} chars", file=sys.stderr)
            return truncated
        return article_text
    
    
    def _call_gpt4o(self, user_prompt: str) -> Dict[str, Any]:
        """Make API call to GPT-4o."""
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0,  # Deterministic for consistency
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content.strip()
        return json.loads(content)
    
    def _validate_extraction(self, extraction: Dict[str, Any]) -> bool:
        """Validate a single extraction result."""
        value = extraction.get("value")
        month = extraction.get("month")
        
        if not month:
            return False
        if value is None:
            return False
        if not (40 <= value <= 80):
            return False
        
        return True
    
    def extract_ssi_values(self, scraped_articles: List[Dict[str, Any]], target_months: List[str]) -> Tuple[Optional[List[Dict]], int, List[Dict]]:
        """
        Extract SSI values from scraped articles using GPT-4o.
        
        Returns:
            (extracted_data, total_articles_processed, discarded_results)
        """
        if not scraped_articles:
            print("⚠️  No scraped articles to process", file=sys.stderr)
            return None, 0, []
        
        all_extractions = []
        discarded_results = []
        total_processed = 0
        
        print("🤖 Processing articles with GPT-4o for SSI extraction...", file=sys.stderr)
        
        for i, article in enumerate(scraped_articles, 1):
            try:
                # Truncate article text to stay within token limits
                article_text = self._truncate_article_text(article['full_text'])
                
                # Build user prompt
                user_prompt = self._build_user_prompt(article, target_months, article_text)
                
                print(f"   🧠 Analyzing article {i}: {article['title'][:50]}...", file=sys.stderr)
                
                # Skip individual article context logs to reduce clutter
                
                # Call GPT-4o
                extracted_data = self._call_gpt4o(user_prompt)
                
                content_preview = str(extracted_data)[:100] + "..." if len(str(extracted_data)) > 100 else str(extracted_data)
                print(f"   📄 GPT-4o response: {content_preview}", file=sys.stderr)
                
                # Process results
                if isinstance(extracted_data, dict) and "results" in extracted_data:
                    results_list = extracted_data["results"]
                    
                    if isinstance(results_list, list) and len(results_list) > 0:
                        for result in results_list:
                            if isinstance(result, dict):
                                # Add article metadata
                                result["source_url"] = article['link']
                                result["source_title"] = article['title']
                                result["source_date"] = article['date']
                                
                                if self._validate_extraction(result):
                                    all_extractions.append(result)
                                    print(f"   ✓ Found SSI: {result.get('month')} = {result.get('value')}%", file=sys.stderr)
                                else:
                                    # Track invalid extractions
                                    discard_reason = self._get_discard_reason(result)
                                    discarded_results.append({
                                        "month": result.get("month"),
                                        "value": result.get("value"),
                                        "reason": discard_reason,
                                        "source_url": article['link'],
                                        "source_title": article['title']
                                    })
                    else:
                        print(f"   ○ No SSI values found in this article", file=sys.stderr)
                
                total_processed += 1
                
            except json.JSONDecodeError as exc:
                print(f"   ⚠️  JSON parsing error for article {i}: {exc}", file=sys.stderr)
            except Exception as exc:
                print(f"   ⚠️  GPT-4o error for article {i}: {exc}", file=sys.stderr)
            
            # Small delay between API calls
            time.sleep(0.5)
        
        # Convert to final output format
        valid_extractions = []
        for extraction in all_extractions:
            valid_extractions.append({
                "month": extraction["month"],
                "level": extraction["value"],
                "confidence": extraction.get("confidence", "medium"),
                "context": extraction.get("context", ""),
                "reasoning": extraction.get("reasoning", ""),
                "source_url": extraction.get("source_url", ""),
                "source_title": extraction.get("source_title", ""),
                "source_date": extraction.get("source_date", "")
            })
        
        return valid_extractions, total_processed, discarded_results
    
    def _get_discard_reason(self, result: Dict[str, Any]) -> str:
        """Get reason why a result was discarded."""
        month = result.get("month")
        value = result.get("value")
        
        if not month:
            return "Missing month"
        elif value is None:
            return "Missing value"
        elif not (40 <= value <= 80):
            return f"Value {value}% outside valid range (40-80%)"
        else:
            return "Unknown validation error"
#!/usr/bin/env python3
"""
Test script to verify Gemini API configuration and rate limits
"""
import os
import asyncio
import time
from datetime import datetime
import google.generativeai as genai

def test_gemini_api():
    """Test Gemini API with different models"""
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    # Configure Gemini
    genai.configure(api_key=api_key)
    
    # List available models
    print("\n📋 Available Gemini Models:")
    try:
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                print(f"  - {model.name}")
    except Exception as e:
        print(f"❌ Error listing models: {e}")
        return False
    
    # Test different models
    test_models = [
        "gemini-2.0-flash-exp",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-pro"
    ]
    
    print("\n🧪 Testing Models:")
    working_model = None
    
    for model_name in test_models:
        try:
            print(f"\n  Testing {model_name}...")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Say 'Hello' in one word")
            print(f"  ✅ {model_name} works!")
            print(f"     Response: {response.text}")
            if not working_model:
                working_model = model_name
        except Exception as e:
            print(f"  ❌ {model_name} failed: {str(e)[:100]}")
    
    if working_model:
        print(f"\n✅ Recommended model: {working_model}")
        return working_model
    else:
        print("\n❌ No working models found")
        return None

async def test_rate_limits(model_name: str):
    """Test Gemini API rate limits"""
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    
    print(f"\n⚡ Testing Rate Limits for {model_name}")
    print("=" * 60)
    
    model = genai.GenerativeModel(model_name)
    
    # Test concurrent requests
    request_counts = [1, 5, 10, 15]
    
    for count in request_counts:
        print(f"\n📊 Testing {count} concurrent requests...")
        start_time = time.time()
        
        try:
            tasks = []
            for i in range(count):
                prompt = f"Count to {i+1}"
                tasks.append(asyncio.to_thread(model.generate_content, prompt))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            elapsed = time.time() - start_time
            successful = sum(1 for r in results if not isinstance(r, Exception))
            failed = count - successful
            
            print(f"  ✅ Successful: {successful}/{count}")
            print(f"  ❌ Failed: {failed}/{count}")
            print(f"  ⏱️  Time: {elapsed:.2f}s")
            print(f"  📈 Rate: {successful/elapsed:.2f} req/s")
            
            if failed > 0:
                print(f"  ⚠️  Errors encountered:")
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        print(f"     Request {i+1}: {str(result)[:80]}")
        
        except Exception as e:
            print(f"  ❌ Test failed: {e}")
        
        # Wait between tests
        if count < request_counts[-1]:
            await asyncio.sleep(2)
    
    print("\n" + "=" * 60)

async def test_query_processing(model_name: str):
    """Test actual query processing like the backend does"""
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    
    print(f"\n🔍 Testing Query Processing with {model_name}")
    print("=" * 60)
    
    model = genai.GenerativeModel(model_name)
    
    test_queries = [
        "Analyze employment trends from 2020 to 2024",
        "Show me GDP growth patterns",
        "Compare unemployment rates across sectors"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Query {i}: {query}")
        start_time = time.time()
        
        try:
            prompt = f"""You are a policy data analysis coordinator. Parse this query into structured JSON:
            
Query: {query}

Return JSON with keys: dataset, year_range, analysis
Example: {{"dataset": "employment", "year_range": "2020-2024", "analysis": "trend"}}"""
            
            response = model.generate_content(prompt)
            elapsed = time.time() - start_time
            
            print(f"  ✅ Success in {elapsed:.2f}s")
            print(f"  📄 Response: {response.text[:200]}")
        
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"  ❌ Failed in {elapsed:.2f}s: {str(e)[:100]}")

def main():
    """Main test function"""
    print("🚀 Gemini API Test Suite")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Test basic API access
    working_model = test_gemini_api()
    
    if not working_model:
        print("\n❌ Cannot proceed - no working models found")
        print("\n💡 Troubleshooting:")
        print("  1. Check GEMINI_API_KEY is set correctly")
        print("  2. Verify API key at https://makersuite.google.com/app/apikey")
        print("  3. Ensure API is enabled in Google Cloud Console")
        return
    
    # Run async tests
    print("\n" + "=" * 60)
    asyncio.run(test_rate_limits(working_model))
    asyncio.run(test_query_processing(working_model))
    
    print("\n" + "=" * 60)
    print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    print(f"\n✅ RECOMMENDED CONFIGURATION:")
    print(f"   DEFAULT_MODEL = '{working_model}'")

if __name__ == "__main__":
    main()

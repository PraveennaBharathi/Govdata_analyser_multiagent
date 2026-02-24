#!/usr/bin/env python3
"""
Comprehensive Gemini API capacity and rate limit testing
"""
import os
import asyncio
import time
from datetime import datetime
import google.generativeai as genai

def test_available_models():
    """List all available Gemini models"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        return None
    
    genai.configure(api_key=api_key)
    
    print("📋 Available Gemini Models:")
    available = []
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            available.append(model.name.replace('models/', ''))
            print(f"  ✅ {model.name}")
    
    return available

def test_model_functionality(model_name):
    """Test if a specific model works"""
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    
    print(f"\n🧪 Testing {model_name}...")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Say 'Hello' in one word")
        print(f"  ✅ SUCCESS: {response.text}")
        return True
    except Exception as e:
        print(f"  ❌ FAILED: {str(e)[:100]}")
        return False

async def test_concurrent_requests(model_name, num_requests):
    """Test concurrent API requests"""
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    
    print(f"\n⚡ Testing {num_requests} concurrent requests...")
    start_time = time.time()
    
    async def make_request(i):
        try:
            result = await asyncio.to_thread(
                model.generate_content,
                f"Count from 1 to {i+1}"
            )
            return {"success": True, "response": result.text[:50]}
        except Exception as e:
            return {"success": False, "error": str(e)[:100]}
    
    tasks = [make_request(i) for i in range(num_requests)]
    results = await asyncio.gather(*tasks)
    
    elapsed = time.time() - start_time
    successful = sum(1 for r in results if r["success"])
    failed = num_requests - successful
    
    print(f"  ✅ Successful: {successful}/{num_requests}")
    print(f"  ❌ Failed: {failed}/{num_requests}")
    print(f"  ⏱️  Time: {elapsed:.2f}s")
    print(f"  📈 Rate: {successful/elapsed:.2f} req/s")
    
    if failed > 0:
        print(f"  ⚠️  Sample errors:")
        for i, r in enumerate(results[:3]):
            if not r["success"]:
                print(f"     {r['error']}")
    
    return successful, failed, elapsed

async def test_query_parsing(model_name):
    """Test actual query parsing like the backend does"""
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    
    print(f"\n🔍 Testing Query Parsing with {model_name}")
    print("=" * 60)
    
    test_queries = [
        "Analyze employment trends from 2020 to 2024",
        "Show me GDP growth patterns over 5 years",
        "Compare unemployment rates across sectors"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Query {i}: {query}")
        start_time = time.time()
        
        try:
            prompt = f"""Parse this query into JSON with keys: dataset, year_range, analysis

Query: {query}

Return only JSON like: {{"dataset": "employment", "year_range": "2020-2024", "analysis": "trend"}}"""
            
            response = model.generate_content(prompt)
            elapsed = time.time() - start_time
            
            print(f"  ✅ Success in {elapsed:.2f}s")
            print(f"  📄 Response: {response.text[:150]}")
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"  ❌ Failed in {elapsed:.2f}s: {str(e)[:100]}")

async def run_capacity_tests(model_name):
    """Run comprehensive capacity tests"""
    print(f"\n{'='*60}")
    print(f"⚡ CAPACITY TESTING: {model_name}")
    print(f"{'='*60}")
    
    # Test increasing concurrent loads
    test_loads = [1, 3, 5, 10, 15, 20]
    results = []
    
    for load in test_loads:
        success, failed, elapsed = await test_concurrent_requests(model_name, load)
        results.append({
            "load": load,
            "success": success,
            "failed": failed,
            "elapsed": elapsed,
            "rate": success/elapsed if elapsed > 0 else 0
        })
        
        # Wait between tests to avoid rate limiting
        if load < test_loads[-1]:
            await asyncio.sleep(3)
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 CAPACITY TEST SUMMARY")
    print(f"{'='*60}")
    print(f"{'Load':<8} {'Success':<10} {'Failed':<8} {'Time':<8} {'Rate (req/s)'}")
    print("-" * 60)
    for r in results:
        print(f"{r['load']:<8} {r['success']:<10} {r['failed']:<8} {r['elapsed']:<8.2f} {r['rate']:<.2f}")
    
    # Recommendations
    max_success_rate = max(r['rate'] for r in results)
    optimal_load = next(r['load'] for r in results if r['rate'] == max_success_rate)
    
    print(f"\n{'='*60}")
    print("💡 RECOMMENDATIONS")
    print(f"{'='*60}")
    print(f"  ✅ Model: {model_name}")
    print(f"  📈 Max throughput: {max_success_rate:.2f} req/s")
    print(f"  🎯 Optimal concurrent requests: {optimal_load}")
    print(f"  ⚠️  Recommended max load: {optimal_load * 0.8:.0f} (80% of optimal)")

def main():
    """Main test execution"""
    print("🚀 Gemini API Capacity Test Suite")
    print("=" * 60)
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Check API key
    if not os.getenv("GEMINI_API_KEY"):
        print("\n❌ GEMINI_API_KEY not set!")
        print("\n💡 Set it with:")
        print("   export GEMINI_API_KEY='your-api-key'")
        return
    
    # List available models
    available = test_available_models()
    if not available:
        return
    
    # Test recommended models
    recommended_models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest"]
    working_model = None
    
    print(f"\n{'='*60}")
    print("🧪 TESTING RECOMMENDED MODELS")
    print(f"{'='*60}")
    
    for model in recommended_models:
        if test_model_functionality(model):
            working_model = model
            break
    
    if not working_model:
        print("\n❌ No working model found!")
        return
    
    print(f"\n✅ Using model: {working_model}")
    
    # Run async tests
    asyncio.run(test_query_parsing(working_model))
    asyncio.run(run_capacity_tests(working_model))
    
    print(f"\n{'='*60}")
    print(f"⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    print(f"\n✅ UPDATE YOUR .env FILE:")
    print(f"   DEFAULT_MODEL={working_model}")

if __name__ == "__main__":
    main()

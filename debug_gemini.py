#!/usr/bin/env python3
"""
Debug script to test Gemini API performance
Run this to check if your Gemini API is working and how fast it responds
"""

import os
import time
import sys

# Set your API key here if not in environment
# os.environ["GEMINI_API_KEY"] = "your-api-key-here"

def test_gemini_performance():
    """Test Gemini API performance and connectivity"""
    
    print("🔍 Testing Gemini API Performance...")
    print("-" * 50)
    
    # Check if API key is set
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") 
    if not api_key:
        print("❌ GOOGLE_API_KEY or GEMINI_API_KEY not found in environment variables")
        print("💡 Set it with: $env:GOOGLE_API_KEY='your-key-here'")
        print("💡 Or: $env:GEMINI_API_KEY='your-key-here'")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    try:
        import google.generativeai as genai
        print("✅ google-generativeai package imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import google-generativeai: {e}")
        print("💡 Install with: pip install google-generativeai")
        return False
    
    try:
        # Configure the API
        start_time = time.time()
        genai.configure(api_key=api_key)
        config_time = time.time() - start_time
        print(f"✅ API configured in {config_time:.2f} seconds")
        
        # Test a simple generation
        print("\n🤖 Testing question generation...")
        
        # Try different model names to find working one
        models_to_try = [
            'models/gemini-1.5-flash',
            'models/gemini-1.5-pro', 
            'models/gemini-2.0-flash',
            'models/gemini-2.5-flash',
            'models/gemini-pro'  # Keep this as fallback even though it might not work
        ]
        
        print("🔍 Checking available models...")
        try:
            available_models = list(genai.list_models())
            print("   Available models:")
            for model in available_models[:5]:  # Show first 5
                print(f"     - {model.name}")
        except Exception as e:
            print(f"   ❌ Could not list models: {e}")
        
        print("\n🧪 Testing model names...")
        working_model = None
        for model_name in models_to_try:
            try:
                print(f"   Trying: {model_name}")
                model = genai.GenerativeModel(model_name)
                
                test_prompt = "Generate 2 simple Python interview questions. Return as a numbered list."
                
                start_time = time.time()
                response = model.generate_content(
                    test_prompt,
                    generation_config=genai.GenerationConfig(
                        max_output_tokens=200,
                        temperature=0.2,
                    )
                )
                generation_time = time.time() - start_time
                
                print(f"   ✅ {model_name} works! Response in {generation_time:.2f} seconds")
                print(f"   📄 Response: {response.text[:100]}...")
                working_model = model_name
                break
                
            except Exception as e:
                print(f"   ❌ {model_name} failed: {str(e)[:100]}...")
        
        if not working_model:
            print("\n❌ No working model found!")
            print("💡 This means your API key may be invalid or you don't have access to these models")
            return False
        
        # If we get here, we found a working model
        print(f"\n✅ Found working model: {working_model}")
        
        # Performance assessment
        print(f"\n📊 Performance Assessment:")
        # Note: generation_time is from the successful model test above
        # We need to do one more test to get timing
        print("🔄 Running final performance test...")
        start_time = time.time()
        model = genai.GenerativeModel(working_model)
        final_response = model.generate_content(
            "Generate 3 technical questions about databases.",
            generation_config=genai.GenerationConfig(
                max_output_tokens=300,
                temperature=0.2,
            )
        )
        final_generation_time = time.time() - start_time
        
        print(f"📄 Final test completed in {final_generation_time:.2f} seconds")
        print(f"📄 Response length: {len(final_response.text)} characters")
        print("\n📋 Sample response:")
        print(final_response.text[:200] + "..." if len(final_response.text) > 200 else final_response.text)
        
        if final_generation_time < 5:
            print("🚀 Excellent - Very fast response")
        elif final_generation_time < 15:
            print("✅ Good - Normal response time")
        elif final_generation_time < 30:
            print("⚠️ Slow - Higher than expected")
        else:
            print("❌ Very slow - May have connectivity issues")
            
        print(f"\n💡 Tips to improve performance:")
        print("1. Use the ⚡ Fast Local generator for instant results")
        print("2. Use AI generation only when you need higher quality questions")
        print("3. Generate questions for fewer technologies at once")
        print(f"4. Update your app to use the working model: {working_model}")
        
        return working_model
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        print("💡 Common issues:")
        print("   - Invalid API key")
        print("   - Network connectivity problems")
        print("   - API quota exceeded")
        print("   - Regional restrictions")
        return False

if __name__ == "__main__":
    print("🔧 Gemini API Debug Tool")
    print("=" * 50)
    result = test_gemini_performance()
    
    if result and result != True:  # result is a working model name
        print(f"\n✅ Gemini API is working correctly!")
        print(f"🎯 Working model found: {result}")
        print("🔧 You should update your app to use this model name.")
    elif result == True:  # Legacy return for older version
        print("\n✅ Gemini API is working correctly!")
        print("🎯 You can now use AI-powered question generation in your app.")
    else:
        print("\n❌ Issues detected with Gemini API")
        print("🔄 The app will fall back to local question generation.")
    
    print("\n" + "=" * 50)
    input("Press Enter to exit...")

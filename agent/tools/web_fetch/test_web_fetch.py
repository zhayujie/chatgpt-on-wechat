"""
Test script for WebFetch tool
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from agent.tools.web_fetch import WebFetch


def test_web_fetch():
    """Test WebFetch tool"""
    
    print("=" * 80)
    print("Testing WebFetch Tool")
    print("=" * 80)
    
    # Create tool instance
    tool = WebFetch()
    
    print(f"\n✅ Tool created: {tool.name}")
    print(f"   Description: {tool.description}")
    
    # Test 1: Fetch a simple webpage
    print("\n" + "-" * 80)
    print("Test 1: Fetching example.com")
    print("-" * 80)
    
    result = tool.execute({
        "url": "https://example.com",
        "extract_mode": "text",
        "max_chars": 1000
    })
    
    if result.status == "success":
        print("✅ Success!")
        data = result.result
        print(f"   Title: {data.get('title', 'N/A')}")
        print(f"   Status: {data.get('status')}")
        print(f"   Extractor: {data.get('extractor')}")
        print(f"   Length: {data.get('length')} chars")
        print(f"   Truncated: {data.get('truncated')}")
        print(f"\n   Content preview:")
        print(f"   {data.get('text', '')[:200]}...")
    else:
        print(f"❌ Failed: {result.result}")
    
    # Test 2: Invalid URL
    print("\n" + "-" * 80)
    print("Test 2: Testing invalid URL")
    print("-" * 80)
    
    result = tool.execute({
        "url": "not-a-valid-url"
    })
    
    if result.status == "error":
        print(f"✅ Correctly rejected invalid URL: {result.result}")
    else:
        print(f"❌ Should have rejected invalid URL")
    
    # Test 3: Test with a real webpage (optional)
    print("\n" + "-" * 80)
    print("Test 3: Fetching a real webpage (Python.org)")
    print("-" * 80)
    
    result = tool.execute({
        "url": "https://www.python.org",
        "extract_mode": "markdown",
        "max_chars": 2000
    })
    
    if result.status == "success":
        print("✅ Success!")
        data = result.result
        print(f"   Title: {data.get('title', 'N/A')}")
        print(f"   Status: {data.get('status')}")
        print(f"   Extractor: {data.get('extractor')}")
        print(f"   Length: {data.get('length')} chars")
        print(f"   Truncated: {data.get('truncated')}")
        if data.get('warning'):
            print(f"   ⚠️  Warning: {data.get('warning')}")
        print(f"\n   Content preview:")
        print(f"   {data.get('text', '')[:300]}...")
    else:
        print(f"❌ Failed: {result.result}")
    
    # Close the tool
    tool.close()
    
    print("\n" + "=" * 80)
    print("Testing complete!")
    print("=" * 80)


if __name__ == "__main__":
    test_web_fetch()

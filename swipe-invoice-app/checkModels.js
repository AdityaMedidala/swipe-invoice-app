const API_KEY = "AIzaSyA2VETqETEadN4z0bS5_j6TvOKCmEvB4nY"; 

async function checkModels() {
  const url = `https://generativelanguage.googleapis.com/v1beta/models?key=${API_KEY}`;
  
  console.log("🔍 Querying Google API for available models...");
  
  try {
    const response = await fetch(url);
    const data = await response.json();

    if (data.error) {
      console.error("❌ API Error:", data.error);
      return;
    }

    if (!data.models) {
      console.log("⚠️ No models found. Is the API enabled?");
      return;
    }

    console.log("\n✅ AVAILABLE MODELS FOR YOUR KEY:");
    console.log("---------------------------------");
    const validModels = data.models
      .filter(m => m.supportedGenerationMethods?.includes("generateContent"))
      .map(m => m.name.replace("models/", "")); // Clean up the name
    
    console.log(validModels.join("\n"));
    console.log("---------------------------------");
    
    // Recommendation logic
    if (validModels.includes("gemini-1.5-pro")) {
      console.log("\n👍 RECOMMENDED: Use 'gemini-1.5-pro'");
    } else if (validModels.includes("gemini-pro")) {
      console.log("\n👍 RECOMMENDED: Use 'gemini-pro' (1.5 might not be enabled)");
    } else {
      console.log("\n⚠️ Use one of the names listed above exactly as shown.");
    }

  } catch (error) {
    console.error("❌ Network Error:", error);
  }
}

checkModels();
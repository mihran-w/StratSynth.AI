import os
import pandas as pd
from PyPDF2 import PdfReader
import openai
import anthropic
import google.generativeai as genai

OPENAI_API_KEY = "YOUR_OPENAI_KEY"
CLAUDE_API_KEY = "YOUR_CLAUDE_KEY"
GEMINI_API_KEY = "YOUR_GEMINI_KEY"

genai.configure(api_key=GEMINI_API_KEY)

def extract_text_from_pdf(pdf_path):
    """Extracts text from the first and last few pages of a PDF paper."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        total_pages = len(reader.pages)
        pages_to_read = list(range(min(5, total_pages))) + list(range(max(0, total_pages-5), total_pages))
        
        for i in sorted(set(pages_to_read)):
            page_text = reader.pages[i].extract_text()
            if page_text:
                text += page_text
        return text
    except Exception as e:
        print(f"Error reading paper {pdf_path}: {e}")
        return ""

def call_openai(prompt, model="gpt-4o"):
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def call_claude(prompt):
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    message = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def call_gemini(prompt):
    model = genai.GenerativeModel('gemini-1.5-pro')
    response = model.generate_content(prompt)
    return response.text

prompt_file_path = "prompts/prompts.xlsx"
prompts_df = pd.read_excel(prompt_file_path)
prompts_dict = dict(zip(prompts_df.iloc[:, 0], prompts_df.iloc[:, 1]))
print(prompts_dict)

folder_path = "papers/"
all_results = []

if not os.path.exists(folder_path):
    print(f"Error: Folder '{folder_path}' not found!")
    exit()

for filename in os.listdir(folder_path):
    if filename.endswith(".pdf"):
        print(f"🚀 Processing Paper: {filename}...")
        file_path = os.path.join(folder_path, filename)
        paper_text = extract_text_from_pdf(file_path)
        
        if not paper_text:
            print(f"⚠️ Skipping {filename}: Extraction failed.")
            continue
        
        row_data = {"Paper Name": filename}
        
        for rq_name, rq_prompt in prompts_dict.items():
            print(f"   🔍 Analyzing {rq_name}...")
            
            full_prompt = f"PAPER CONTENT:\n{paper_text}\n\nINSTRUCTION:\n{rq_prompt}"
            
            try:
                row_data[f"{rq_name}_GPT"] = call_openai(full_prompt)
                row_data[f"{rq_name}_Claude"] = call_claude(full_prompt)
                row_data[f"{rq_name}_Gemini"] = call_gemini(full_prompt)
            except Exception as e:
                print(f"   ❌ API Error for {rq_name}: {e}")
                row_data[f"{rq_name}_GPT"] = "Error"
                row_data[f"{rq_name}_Claude"] = "Error"
                row_data[f"{rq_name}_Gemini"] = "Error"
            
        all_results.append(row_data)

output_df = pd.DataFrame(all_results)
output_df.to_excel("StratSynth_Final_Analysis.xlsx", index=False)
print("\n✅ Process Completed! Check 'StratSynth_Final_Analysis.xlsx'.")
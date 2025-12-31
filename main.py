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
    try:
        reader = PdfReader(pdf_path)
        text = ""
        total_pages = len(reader.pages)
        pages_to_read = list(range(min(5, total_pages))) + list(range(max(0, total_pages-5), total_pages))
        for i in sorted(set(pages_to_read)):
            page_text = reader.pages[i].extract_text()
            if page_text: text += page_text
        return text
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
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

def call_gemini(prompt):
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(prompt)
    return response.text


prompt_file_path = "prompts/prompts.xlsx"
prompts_df = pd.read_excel(prompt_file_path)
prompts_dict = dict(zip(prompts_df.iloc[:, 0], prompts_df.iloc[:, 1]))

folder_path = "papers/"
results_gpt = []
results_claude = []
results_gemini = []

for filename in os.listdir(folder_path):
    if filename.endswith(".pdf"):
        print(f"🚀 Processing: {filename}")
        paper_text = extract_text_from_pdf(os.path.join(folder_path, filename))
        
        if not paper_text: continue

        res_gpt = {"Paper Name": filename}
        res_claude = {"Paper Name": filename}
        res_gemini = {"Paper Name": filename}

        for rq_name, rq_prompt in prompts_dict.items():
            full_prompt = f"PAPER CONTENT:\n{paper_text}\n\nINSTRUCTION:\n{rq_prompt}"
            
            try:
                print(f"   🔍 Analyzing {rq_name} with Gemini...")
                res_gemini[rq_name] = call_gemini(full_prompt)
                
                res_gpt[rq_name] = call_openai(full_prompt)
                res_claude[rq_name] = call_claude(full_prompt)
            except Exception as e:
                print(f"   ❌ Error: {e}")
                res_gemini[rq_name] = "Error"

        results_gemini.append(res_gemini)
        results_gpt.append(res_gpt)
        results_claude.append(res_claude)

with pd.ExcelWriter("StratSynth_Final_Analysis.xlsx", engine="xlsxwriter") as writer:
    if results_gemini:
        pd.DataFrame(results_gemini).to_excel(writer, sheet_name="Gemini_Results", index=False)
    if results_gpt:
        pd.DataFrame(results_gpt).to_excel(writer, sheet_name="GPT_Results", index=False)
    if results_claude:
        pd.DataFrame(results_claude).to_excel(writer, sheet_name="Claude_Results", index=False)

print("\n✅ Process Completed! Check 'StratSynth_Final_Analysis.xlsx'.")
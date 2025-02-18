import openai
import fitz  # PyMuPDF for PDF processing
import docx
import pandas as pd
import re  # ✅ Regular expressions (built-in, no installation needed)


def extract_text(files, summarize=False, user_plan="The Foundation (Free)"):
    """
    Extracts text from multiple PDF and DOCX files.
    Optionally summarizes long documents based on user plan.
    """
    extracted_texts = {}
    max_doc_tokens = 2000 if user_plan in ["Enterprise", "Growth"] else 1000

    for file in files:
        try:
            if file.name.endswith(".pdf"):
                with fitz.open(stream=file, filetype="pdf") as doc:
                    extracted_text = "\n".join([page.get_text("text") for page in doc])

            elif file.name.endswith(".docx"):
                doc = docx.Document(file)
                extracted_text = "\n".join([para.text for para in doc.paragraphs])

            else:
                extracted_text = f"Unsupported file format: {file.name}"

        except Exception as e:
            extracted_text = f"Error extracting text from {file.name}: {str(e)}"

        # ✅ Ensure meaningful fallback if empty
        if not extracted_text.strip():
            extracted_text = "No content extracted."

        # ✅ Summarize if necessary
        if summarize and len(extracted_text) > max_doc_tokens:
            extracted_text = summarize_text(extracted_text, max_tokens=max_doc_tokens)

        extracted_texts[file.name] = extracted_text  # ✅ Store extracted text

    return extracted_texts

def extract_financial_data(files, summarize=False, user_plan="The Foundation (Free)"):
    """
    Extracts structured financial data from Excel (XLSX) or CSV files.
    Optionally summarizes large datasets based on user plan.
    """
    extracted_data = {}
    max_rows = 2000 if user_plan in ["Enterprise", "Growth"] else 1000

    for file in files:
        try:
            if file.name.endswith(".xlsx") or file.name.endswith(".csv"):
                df = pd.read_excel(file) if file.name.endswith(".xlsx") else pd.read_csv(file)

                if df.empty:
                    extracted_text = "📊 No financial data extracted."
                else:
                    summary = df.describe().to_string()
                    extracted_text = f"📊 Financial Data Summary:\n{summary}"

                    if summarize and len(df) > max_rows:
                        extracted_text += f"\n\n📉 (Limited to {max_rows} rows for summarization)"
                        extracted_text += "\n" + df.head(max_rows).to_string()

            else:
                extracted_text = f"⚠️ Unsupported file format: {file.name}"

        except Exception as e:
            extracted_text = f"❌ Error processing {file.name}: {str(e)}"

        if not extracted_text.strip():
            extracted_text = "📊 No financial data extracted."

        extracted_data[file.name] = extracted_text  # ✅ Store extracted text

    return extracted_data

def pre_screen_documents(extracted_texts):
    """
    Pre-screens documents to determine relevance, contradictions, and compatibility.
    """
    if len(extracted_texts) < 3:
        return "🔍 Not enough documents for pre-screening."

    def truncate_text(text, max_chars=8000):
        """Safely truncates text while ensuring whole sentences are preserved."""
        if len(text) <= max_chars:
            return text
        return text[:max_chars].rsplit('.', 1)[0] + "..."  # ✅ Stops at last full sentence

    combined_texts = truncate_text("\n\n".join(extracted_texts.values()), max_chars=8000)

    pre_screen_prompt = f"""
    You are an AI document analyst. Assess the relationship between these documents:

    1️⃣ **Are the documents thematically related?**  
    2️⃣ **Do they contain contradictory information?**  
    3️⃣ **Are any documents irrelevant to the others?**  
    4️⃣ **Summarize how these documents interconnect.**  

    📂 **Documents Included:** {len(extracted_texts)}  
    📖 **Document Content (Condensed):**  
    {combined_texts}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": pre_screen_prompt}]
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"Pre-screening failed: {str(e)}"

def analyze_patterns(extracted_texts, max_chars=5000):
    """
    Performs AI-powered pattern recognition if 3 or more documents are uploaded.
    Prioritizes key sections before truncating.
    """
    if len(extracted_texts) < 3:
        return "🔍 Not enough documents for AI pattern recognition."

    def extract_relevant_sections(text, max_length=2500):
        """
        Extracts key sections from a document: beginning, conclusion, and important headings.
        """
        # ✅ Extract first 20% (introduction) and last 20% (conclusion)
        first_part = text[:max_length // 2]
        last_part = text[-(max_length // 2):]

        # ✅ Prioritize key sentences containing 'Summary', 'Conclusion', 'Findings', 'Results'
        important_sentences = re.findall(r'([^.]*?(Summary|Conclusion|Findings|Results|Insights)[^.]*\.)', text, re.IGNORECASE)
        important_text = " ".join([sent[0] for sent in important_sentences])[:max_length // 2]

        # ✅ Combine sections: Important Sentences + First 20% + Last 20%
        combined = f"{important_text}\n\n{first_part}\n\n{last_part}"
        return combined[:max_length]  # ✅ Ensure final text does not exceed limit

    # ✅ Apply priority-based truncation
    truncated_texts = [extract_relevant_sections(text, max_chars // len(extracted_texts)) for text in extracted_texts.values()]

    combined_texts = "\n\n".join(truncated_texts)

    pattern_prompt = f"""
    You are an AI document analyst. Identify patterns across the following documents:

    📂 **Documents Included:** {len(extracted_texts)}
    📖 **Condensed Document Content:**  
    {combined_texts}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": pattern_prompt}]
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"AI pattern analysis failed: {str(e)}"

def summarize_text(text, max_tokens=1000):
    """
    Summarizes extracted text to reduce token count before sending to OpenAI.
    """
    if not text:
        return "No text to summarize."

    summary_prompt = f"Summarize this document within {max_tokens} tokens:\n\n{text[:5000]}"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": summary_prompt}]
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"Summarization failed: {str(e)}"

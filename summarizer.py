(venv) root@elnidodelaguila:/home/torrefacto/book-summarizer# cat summarizer.py
import re
import json
import shutil
import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, Any
from pydantic import BaseModel
from termcolor import colored
from datetime import datetime
from openai import OpenAI

# ========================
# Configuración
# ========================
PDF_NAME = "meditations.pdf"

BASE_DIR = Path("book_analysis")
PDF_DIR = BASE_DIR / "pdfs"
KNOWLEDGE_DIR = BASE_DIR / "knowledge_bases"
SUMMARIES_DIR = BASE_DIR / "summaries"

PDF_PATH = PDF_DIR / PDF_NAME
OUTPUT_PATH = KNOWLEDGE_DIR / f"{PDF_NAME.replace('.pdf', '_knowledge.json')}"

MODEL = "gpt-4o-mini"
TEST_PAGES = 60  # None para procesar todo el PDF

# Regex para reconocer "Part X"
PART_PATTERN = re.compile(r"^\s*Part\s+", re.IGNORECASE)
# Regex para reconocer "Chapter X"
CHAPTER_PATTERN = re.compile(r"^\s*Chapter\s+\d+", re.IGNORECASE)

# ========================
# Clases y funciones
# ========================
class PageContent(BaseModel):
    has_content: bool
    knowledge: list[str]


def print_instructions():
    print(colored("""
==========================
PDF Book Analysis Tool
==========================
- Crea carpeta solo para:
  1) Part X (nivel=1)
  2) Chapter X (nivel=2)
- El resto se guarda como .md suelto
""", "cyan"))


def setup_directories():
    for directory in [KNOWLEDGE_DIR, SUMMARIES_DIR]:
        if directory.exists():
            for file in directory.glob("*"):
                if file.is_file():
                    file.unlink()

    for directory in [PDF_DIR, KNOWLEDGE_DIR, SUMMARIES_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    if not PDF_PATH.exists():
        source_pdf = Path(PDF_NAME)
        if source_pdf.exists():
            shutil.copy2(source_pdf, PDF_PATH)
            print(colored(f"📄 Copied PDF to analysis directory: {PDF_PATH}", "green"))
        else:
            raise FileNotFoundError(f"PDF file {PDF_NAME} not found")


def load_or_create_knowledge_base() -> Dict[str, Any]:
    if OUTPUT_PATH.exists():
        with open(OUTPUT_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_knowledge_base(kb: Dict[str, Any]):
    print(colored("💾 Saving knowledge base ...", "blue"))
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(kb, f, indent=2)


def process_page(client: OpenAI, page_text: str) -> PageContent:
    completion = client.beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": """Analyze this page as an expert student:

                SKIP if page contains:
                - Structural elements (indexes, TOC, references)
                - Editorial info (copyright, publishing details)
                - Blank pages or non-educational content

                EXTRACT if page contains:
                - Key concepts and definitions
                - Important arguments and theories
                - Practical examples and case studies
                - Methodologies and frameworks
                - Significant findings
                - Critical analysis

                Format requirements:
                - Extract detailed, actionable knowledge points
                - Include important verbatim quotes
                - Preserve technical terminology
                - Provide context where needed"""

            },
            {
                "role": "user",
                "content": f"Page text: {page_text}"
            }
        ],
        response_format=PageContent
    )
    return completion.choices[0].message.parsed


def analyze_knowledge(client: OpenAI, title: str, knowledge_points: list[str]) -> str:
    if not knowledge_points:
        return ""
    print(colored(f"🤔 Generating analysis for '{title}'...", "cyan"))
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": """
You are an expert educator tasked with summarizing and simplifying a technical document for students learning this subject. 
Your goal is to make the material engaging, easy to understand, and clear.

Follow these guidelines:
1. **Simplify concepts**: Use plain language and avoid jargon unless necessary. Define terms clearly and use analogies if helpful.
2. **Structure effectively**: Use the following Markdown conventions:
   - `##` for main sections.
   - `###` for subsections.
   - Bullet points for lists.
   - **Bold** for important terms and *italic* for terminology.
   - Include diagrams using Mermaid (`mindmap`, `flowchart`, etc.) or ASCII art if applicable.
3. **Engage and clarify**:
   - Use emojis to highlight key points (e.g., 💡 for insights, ⚠️ for warnings, 📖 for examples).
   - Provide examples and real-world analogies.
   - Add summaries, key takeaways, and tips for studying at the end of each section.
4. **Be concise but thorough**: Summarize all the key knowledge points while maintaining clarity.

Based on these guidelines, generate a student-friendly summary for the title: '{title}'.
"""
            },
            {
                "role": "user",
                "content": f"Knowledge points:\n" + "\n".join(knowledge_points)
            }
        ]
    )
    print(colored(f"✨ Analysis generated for '{title}'!", "green"))
    return completion.choices[0].message.content


def save_md(folder: Path, filename_prefix: str, title: str, markdown_text: str):
    if not markdown_text.strip():
        print(colored(f"⏭️  Skipping '{title}' -> no content", "yellow"))
        return

    safe_name = re.sub(r"[^\w-]+", "-", title.lower()).strip("-")
    md_path = folder / f"{filename_prefix}-{safe_name}.md"

    content = f"""# {title}
Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

{markdown_text}

---
*Analysis generated using AI Book Analysis Tool*
"""
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(colored(f"✅ Saved: {md_path}", "green"))


def main():
    print_instructions()
    input(colored("Press Enter to continue or Ctrl+C to exit...", "yellow"))

    setup_directories()
    client = OpenAI()

    # Abrimos el PDF
    doc = fitz.open(PDF_PATH)
    total_pages = doc.page_count
    limit_pages = TEST_PAGES if TEST_PAGES else total_pages

    print(colored(f"PDF has {total_pages} pages. We'll process up to {limit_pages}.", "cyan"))

    toc = doc.get_toc()  # [[level, title, page], ...]
    if not toc:
        # fallback
        toc = [[1, "Part I (Entire PDF)", 1]]

    # knowledge_base con estructura:
    # {
    #    "Part I. ...": {
    #       "start": X, "end": Y,
    #       "part_knowledge": [],
    #       "chapters": {
    #         "Chapter 1. ...": {
    #           "start": A, "end": B,
    #           "chapter_knowledge": [],
    #           "sections": [... secciones en .md...]
    #         }
    #       },
    #       "other_sections": [...] # secciones sin "Chapter" -> .md sueltos
    #    },
    #    ...
    # }

    knowledge_base = load_or_create_knowledge_base()

    parts = []
    current_part = None

    for i, (level, title, page_num) in enumerate(toc):
        start_idx = page_num - 1

        # 1) Detectar "Part" a nivel=1 -> nueva carpeta
        if level == 1 and PART_PATTERN.search(title):
            # cerramos part anterior
            if current_part:
                parts.append(current_part)

            current_part = {
                "title": title,
                "start": start_idx,
                "end": None,
                "part_knowledge": [],
                "chapters": {},
                "other_sections": []  # Secciones del part que no sean "Chapter..."
            }

        # 2) Detectar "Chapter" a nivel=2 -> subcarpeta
        elif level == 2 and CHAPTER_PATTERN.search(title) and current_part:
            # Creamos un diccionario para ese chapter
            current_part["chapters"][title] = {
                "start": start_idx,
                "end": None,
                "chapter_knowledge": [],
                "sections": []  # sub-subsecciones
            }

        # 3) Otras secciones
        else:
            if current_part:
                # Miramos si cae dentro del chapter actual
                # El "chapter actual" sería el último que hayamos detectado
                # dentro de current_part["chapters"]
                chapters_in_part = list(current_part["chapters"].keys())
                if chapters_in_part:
                    last_chapter_title = chapters_in_part[-1]
                    # si level >=3, o es level=2 sin "Chapter"
                    current_part["chapters"][last_chapter_title]["sections"].append({
                        "title": title,
                        "level": level,
                        "start": start_idx,
                        "end": None,
                        "knowledge": []
                    })
                else:
                    # No tenemos chapter actual -> es una sección suelta en el "Part"
                    current_part["other_sections"].append({
                        "title": title,
                        "level": level,
                        "start": start_idx,
                        "end": None,
                        "knowledge": []
                    })
            else:
                # No hay part actual -> ignorar
                pass

    if current_part:
        parts.append(current_part)

    # Determinar end_page para cada part, cada chapter y cada seccion
    for idx in range(len(parts)):
        if idx + 1 < len(parts):
            parts[idx]["end"] = parts[idx+1]["start"] - 1
        else:
            parts[idx]["end"] = total_pages - 1

        # chapters
        part_chapters = parts[idx]["chapters"]
        chap_titles = list(part_chapters.keys())
        for c_idx, c_title in enumerate(chap_titles):
            if c_idx + 1 < len(chap_titles):
                part_chapters[c_title]["end"] = part_chapters[chap_titles[c_idx + 1]]["start"] - 1
            else:
                # hasta el end del part
                part_chapters[c_title]["end"] = parts[idx]["end"]

            # secciones
            sub_secs = part_chapters[c_title]["sections"]
            for s_idx in range(len(sub_secs)):
                if s_idx + 1 < len(sub_secs):
                    sub_secs[s_idx]["end"] = sub_secs[s_idx+1]["start"] - 1
                else:
                    sub_secs[s_idx]["end"] = part_chapters[c_title]["end"]

        # Otras secciones sueltas en el part
        other_secs = parts[idx]["other_sections"]
        for s_idx in range(len(other_secs)):
            if s_idx + 1 < len(other_secs):
                other_secs[s_idx]["end"] = other_secs[s_idx+1]["start"] - 1
            else:
                other_secs[s_idx]["end"] = parts[idx]["end"]

    # ================
    # Recorrido de páginas
    # ================
    for part_info in parts:
        p_start = part_info["start"]
        p_end = min(part_info["end"], limit_pages - 1)

        print(colored(f"Processing Part '{part_info['title']}' (p. {p_start+1}-{p_end+1})", "magenta"))

        # Prepara knowledge base para este part
        knowledge_base[part_info["title"]] = {
            "start": p_start,
            "end": p_end,
            "part_knowledge": [],
            "chapters": {},
            "other_sections": []
        }

        # Convertimos dict => lista (chapter_info) para iterar
        chapters_list = []
        for ctitle, cdict in part_info["chapters"].items():
            chapters_list.append((ctitle, cdict))
        # Otras secciones
        other_list = part_info["other_sections"]  # array de dicts

        # Recorremos las páginas del Part
        for page_i in range(p_start, p_end + 1):
            if page_i >= limit_pages:
                break
            page = doc[page_i]
            text = page.get_text()
            result = process_page(client, text)
            if not result.has_content:
                print(colored(f"  ⏭️  Skipping page {page_i+1}", "yellow"))
                continue

            # Determinamos si cae dentro de un Chapter, Subcapítulo, o "other_sections"
            in_chapter = False

            # Orden inverso (por si hay solapamiento)
            for (ch_title, ch_data) in reversed(chapters_list):
                c_s = ch_data["start"]
                c_e = ch_data["end"]
                if c_s <= page_i <= c_e:
                    # Está dentro de este chapter
                    in_chapter = True
                    # Revisar si hay sub-sección
                    in_sub = False
                    for sub_sec in ch_data["sections"]:
                        if sub_sec["start"] <= page_i <= sub_sec["end"]:
                            sub_sec["knowledge"].extend(result.knowledge)
                            print(colored(f"    ✅ Page {page_i+1}: {len(result.knowledge)} pts -> Subsection '{sub_sec['title']}' (Chapter '{ch_title}')", "green"))
                            in_sub = True
                            break
                    if not in_sub:
                        # Añadimos a chapter-level
                        ch_data["chapter_knowledge"].extend(result.knowledge)
                        print(colored(f"    ✅ Page {page_i+1}: {len(result.knowledge)} pts -> Chapter-level '{ch_title}'", "green"))
                    break

            if not in_chapter:
                # Miramos si entra en other_sections
                in_other = False
                for sec in reversed(other_list):
                    if sec["start"] <= page_i <= sec["end"]:
                        sec["knowledge"].extend(result.knowledge)
                        in_other = True
                        print(colored(f"    ✅ Page {page_i+1}: {len(result.knowledge)} pts -> Part-level Subsection '{sec['title']}'", "green"))
                        break

                if not in_other:
                    # Part-level sin seccion
                    part_info["part_knowledge"].extend(result.knowledge)
                    print(colored(f"    ✅ Page {page_i+1}: {len(result.knowledge)} pts -> Part-level (no subsec)", "green"))

        # Volcar a knowledge_base
        kb_part = knowledge_base[part_info["title"]]
        kb_part["part_knowledge"] = part_info["part_knowledge"][:]

        # Chapters
        for ch_title, ch_dict in chapters_list:
            kb_part["chapters"][ch_title] = {
                "start": ch_dict["start"],
                "end": ch_dict["end"],
                "chapter_knowledge": ch_dict["chapter_knowledge"][:],
                "sections": []
            }
            # Secciones
            for ssec in ch_dict["sections"]:
                kb_part["chapters"][ch_title]["sections"].append({
                    "title": ssec["title"],
                    "start": ssec["start"],
                    "end": ssec["end"],
                    "knowledge": ssec["knowledge"][:]
                })

        # Otras secciones
        kb_part["other_sections"] = []
        for o_sec in other_list:
            kb_part["other_sections"].append({
                "title": o_sec["title"],
                "start": o_sec["start"],
                "end": o_sec["end"],
                "knowledge": o_sec["knowledge"][:]
            })

    # ================
    # Generar .md
    # ================
    for part_info in parts:
        p_title = part_info["title"]
        kb_part = knowledge_base[p_title]
        # Carpeta del "Part"
        part_folder = SUMMARIES_DIR / re.sub(r"[^\w-]+", "-", p_title.lower())
        part_folder.mkdir(parents=True, exist_ok=True)

        # (1) README.md del Part (combina part_knowledge + other_sections + chapters?)
        part_combined = kb_part["part_knowledge"][:]
        # sumamos las "other_sections"
        for osec in kb_part["other_sections"]:
            part_combined.extend(osec["knowledge"])

        # No sumamos los capítulos, pues cada Chapter tendrá su propia subcarpeta
        readme_part = analyze_knowledge(client, f"{p_title} (Overview)", part_combined)
        save_md(part_folder, "00", "README", readme_part)

        # (2) Generar un .md para cada "other_section"
        for idx_s, osec in enumerate(kb_part["other_sections"], start=1):
            if not osec["knowledge"]:
                continue
            prefix = f"{idx_s:02d}"
            s_markdown = analyze_knowledge(client, osec["title"], osec["knowledge"])
            save_md(part_folder, prefix, osec["title"], s_markdown)

        # (3) Para cada Chapter -> subcarpeta
        chapter_titles = list(kb_part["chapters"].keys())
        for chap_i, chap_t in enumerate(chapter_titles, start=1):
            chap_data = kb_part["chapters"][chap_t]
            # crear subcarpeta
            chap_folder = part_folder / re.sub(r"[^\w-]+", "-", chap_t.lower())
            chap_folder.mkdir(parents=True, exist_ok=True)

            # readme del chapter
            combined_chap = chap_data["chapter_knowledge"][:]
            # sumamos subsecciones
            for subsec in chap_data["sections"]:
                combined_chap.extend(subsec["knowledge"])

            chapter_overview = analyze_knowledge(client, f"{chap_t} (Overview)", combined_chap)
            save_md(chap_folder, "00", "README", chapter_overview)

            # secciones sueltas
            for s_idx, ssec in enumerate(chap_data["sections"], start=1):
                if not ssec["knowledge"]:
                    continue
                prefix = f"{s_idx:02d}"
                s_text = analyze_knowledge(client, ssec["title"], ssec["knowledge"])
                save_md(chap_folder, prefix, ssec["title"], s_text)

    # Guardar JSON final
    save_knowledge_base(knowledge_base)
    print(colored("\n✨ All chapters processed! ✨", "green", attrs=['bold']))


if __name__ == "__main__":
    main()


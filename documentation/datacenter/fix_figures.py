#!/usr/bin/env python3
import os
import json

figures_dir = "/Users/starschich/hids/documentation/datacenter/figures"
tex_sections_dir = "/Users/starschich/hids/documentation/datacenter/sections"

with open(os.path.join(figures_dir, "figure_map.json"), "r") as f:
    figure_map = json.load(f)

print("Figure map:", figure_map)

# Define the remaining replacements with exact strings
replacements = {
    "2": {
        "filename": figure_map.get("fig2", ""),
        "caption": "A 75\\% increase in TDP power, but a 50x increase in performance",
        "label": "fig:performance-increase",
        "old_start": "\\begin{figure}[h]\n\\centering\n% TODO: Insert Figure 2 from source document\n\\framebox[0.8\\textwidth][c]{\\parbox[c][4cm][c]{0.7\\textwidth}{Figure 2: A 75\\% increase in TDP power, but a 50x increase in performance}}\n\\caption{A 75\\% increase in TDP power, but a 50x increase in performance}\n\\label{fig:performance-increase}\n\\end{figure}",
    },
    "4": {
        "filename": figure_map.get("fig4", ""),
        "caption": "GPU Load Swings during an LLM workload",
        "label": "fig:gpu-load-swing",
        "old_start": "\\begin{figure}[h]\n\\centering\n% TODO: Insert Figure 4 from source document\n\\framebox[0.8\\textwidth][c]{\\parbox[c][4cm][c]{0.7\\textwidth}{Figure 4: GPU Load Swings during an LLM workload \\\\\\\n and Power Envelope over a full compute cycle}}\n\\caption{GPU Load Swings during an LLM workload}\n\\label{fig:gpu-load-swing}\n\\end{figure}",
    },
    "9": {
        "filename": figure_map.get("fig9", ""),
        "caption": "DC/DC with symmetrical fusing and hotswap controllers to allow for \\$\\pm400 VDC or 800 VDC sources",
        "label": "fig:dc-dc-fusing",
        "old_start": "\\begin{figure}[h]\n\\centering\n% TODO: Insert Figure 9 from source document\n\\framebox[0.8\\textwidth][c]{\\parbox[c][4cm][c]{0.7\\textwidth}{Figure 9: DC/DC with symmetrical fusing and hotswap controllers}}\n\\caption{DC/DC with symmetrical fusing and hotswap controllers to allow for \\$\\pm400 VDC or 800 VDC sources}\n\\label{fig:dc-dc-fusing}\n\\end{figure}",
    },
    "10": {
        "filename": figure_map.get("fig10", ""),
        "caption": "Datacenter architecture over time",
        "label": "fig:evolution",
        "old_start": "\\begin{figure}[h]\n\\centering\n% TODO: Insert Figure 10 from source document\n\\framebox[0.8\\textwidth][c]{\\parbox[c][6cm][c]{0.7\\textwidth}{Figure 10: Datacenter architecture over time \\\\\\\n (415 VAC \\$\\rightarrow\\$ 800 VDC side power \\$\\rightarrow\\$ 800 VDC facility \\$\\rightarrow\\$ MV Rectifier/SST)}}\n\\caption{Datacenter architecture over time}\n\\label{fig:evolution}\n\\end{figure}",
    },
}

def create_new_block(filename, caption, label):
    return f"""\\begin{{figure}}[h]
\\centering
\\includegraphics[width=0.8\\textwidth]{{figures/{filename}}}
\\caption{{{caption}}}
\\label{{{label}}}
\\end{{figure}}"""

# Now update the .tex files
updated_files = []

for section_file in sorted(os.listdir(tex_sections_dir)):
    if section_file.endswith(".tex"):
        filepath = os.path.join(tex_sections_dir, section_file)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            modified = False
            new_content = content
            
            for fig_num, data in replacements.items():
                if data["filename"] and len(data["filename"]) > 0:
                    old_block = data["old_start"]
                    new_block = create_new_block(data["filename"], data["caption"], data["label"])
                    
                    if old_block in new_content:
                        new_content = new_content.replace(old_block, new_block)
                        modified = True
                        print(f"Updated {section_file}: Replaced Figure {fig_num}")
            
            if modified:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                updated_files.append(section_file)
                
        except Exception as e:
            print(f"Error processing {section_file}: {e}")

print(f"\nUpdated {len(updated_files)} section files: {', '.join(updated_files) if updated_files else 'none'}")

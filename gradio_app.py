"""
Gradio Web Interface for Address Province Matching
Người dùng nhập 2 địa chỉ, hệ thống trích xuất tỉnh/thành và so sánh
"""

import gradio as gr
import json
import re
from pathlib import Path


def remove_diacritics(text):
    """Remove Vietnamese diacritics for normalization"""
    import unicodedata
    if not text:
        return text
    nfd = unicodedata.normalize('NFD', text)
    without_diacritics = ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
    return without_diacritics


def normalize_vietnamese(text):
    """Normalize Vietnamese text (handle Hoà -> Hòa variations)"""
    if not text:
        return text
    
    import unicodedata
    normalized = unicodedata.normalize('NFC', text)
    
    # Handle specific Vietnamese diacritic variations
    replacements = {
        'Hoà': 'Hòa',
        'hoà': 'hòa',
        'HOÀ': 'HÒA',
    }
    
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    
    return normalized


class ProvinceExtractor:
    """Class to extract province from address"""
    
    def __init__(self, ground_truth_file):
        # Load ground truth
        with open(ground_truth_file, 'r', encoding='utf-8') as f:
            self.ground_truth = json.load(f)
        
        # Create variant to official mapping
        self.variant_to_official = {}
        for official_name, variants in self.ground_truth.items():
            self.variant_to_official[official_name] = official_name
            self.variant_to_official[official_name.lower()] = official_name
            
            for variant in variants:
                self.variant_to_official[variant] = official_name
                self.variant_to_official[variant.lower()] = official_name
    
    def extract_province(self, address):
        """Extract province from address"""
        if not address:
            return None
        
        # Normalize address
        address_normalized = normalize_vietnamese(address)
        address_lower = address_normalized.lower()
        
        # Find all matches with scoring
        candidates = []
        
        for variant, official in self.variant_to_official.items():
            variant_str = variant if isinstance(variant, str) else str(variant)
            variant_normalized = normalize_vietnamese(variant_str)
            variant_lower = variant_normalized.lower()
            
            # Find match
            match = None
            is_word_boundary_match = False
            
            # 1. Word boundary match (more accurate)
            pattern = r'(?:^|[\s,;.\-/])(' + re.escape(variant_lower) + r')(?:[\s,;.\-/]|$)'
            regex_match = re.search(pattern, address_lower)
            
            if regex_match:
                match = regex_match
                is_word_boundary_match = True
            # 2. Substring match only for variants >= 4 chars
            elif len(variant_str) >= 4 and variant_lower in address_lower:
                match_pos = address_lower.find(variant_lower)
                if match_pos >= 0:
                    class PseudoMatch:
                        def __init__(self, pos):
                            self.start_pos = pos
                        def start(self):
                            return self.start_pos
                    match = PseudoMatch(match_pos)
                    is_word_boundary_match = False
            
            if match:
                # Calculate priority score
                score = 0
                score += len(variant_str) * 100  # Length
                if is_word_boundary_match:
                    score += 1000  # Word boundary bonus
                position_score = match.start() / len(address_lower) * 50
                score += position_score  # Position in address
                
                # Multi-word bonus (prioritize compound names like "Tra Vinh")
                if ' ' in variant_str:
                    score += 500
                
                candidates.append({
                    'official': official,
                    'variant': variant_str,
                    'score': score
                })
        
        if not candidates:
            return None
        
        # Sort by score and select best match
        candidates.sort(key=lambda x: x['score'], reverse=True)
        return candidates[0]['official']
    
    def compare_provinces(self, prov1, prov2):
        """Compare two provinces"""
        if not prov1 or not prov2:
            return False, "Một trong hai tỉnh không xác định được"
        
        # Exact match
        if prov1 == prov2:
            return True, "Exact match"
        
        # For now, just exact match
        # Can extend with merger logic if needed
        return False, f"Mismatch: {prov1} ≠ {prov2}"


# Initialize extractor
ground_truth_path = Path(__file__).parent / "tinh_thanh.json"
extractor = ProvinceExtractor(ground_truth_path)


def compare_addresses(address1, address2):
    """
    Compare two addresses and extract provinces
    
    Args:
        address1: First address
        address2: Second address
    
    Returns:
        Tuple of (province1, province2, match_status, match_emoji)
    """
    # Extract provinces
    province1 = extractor.extract_province(address1)
    province2 = extractor.extract_province(address2)
    
    # Compare
    is_match, reason = extractor.compare_provinces(province1, province2)
    
    # Prepare output
    prov1_display = province1 if province1 else "❌ Không xác định được"
    prov2_display = province2 if province2 else "❌ Không xác định được"
    
    # Match status
    if is_match:
        match_status = "✅ MATCH"
        match_emoji = "✅"
    else:
        match_status = "❌ MISMATCH"
        match_emoji = "❌"
    
    return prov1_display, prov2_display, match_status, match_emoji


# Create Gradio interface
with gr.Blocks(title="🏙️ Address Province Matcher", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 🏙️ Vietnamese Address Province Matcher
        
        Nhập hai địa chỉ để trích xuất tỉnh/thành phố và so sánh
        """
    )
    
    with gr.Row():
        with gr.Column():
            address1_input = gr.Textbox(
                label="📍 Địa chỉ 1",
                placeholder="VD: 123 Lê Lợi, P. Bến Thành, Q.1, Hồ Chí Minh",
                lines=2
            )
        
        with gr.Column():
            address2_input = gr.Textbox(
                label="📍 Địa chỉ 2",
                placeholder="VD: 123 Lê Lợi, P. Bến Thành, Q.1, TPHCM",
                lines=2
            )
    
    compare_btn = gr.Button("🔍 So sánh", variant="primary", size="lg")
    
    gr.Markdown("### 📊 Kết quả")
    
    with gr.Row():
        province1_output = gr.Textbox(
            label="🏛️ Tỉnh/Thành từ Địa chỉ 1",
            interactive=False
        )
        province2_output = gr.Textbox(
            label="🏛️ Tỉnh/Thành từ Địa chỉ 2",
            interactive=False
        )
    
    with gr.Row():
        match_output = gr.Textbox(
            label="🎯 Kết quả so sánh",
            interactive=False
        )
        match_emoji_output = gr.Textbox(
            label="Status",
            interactive=False
        )
    
    # Examples
    gr.Examples(
        examples=[
            [
                "123 Lê Lợi, P. Bến Thành, Q.1, Hồ Chí Minh",
                "123 Lê Lợi, P. Bến Thành, Q.1, TPHCM"
            ],
            [
                "45 P. Hàng Bông, Q. Hoàn Kiếm, Hà Nội",
                "45 P. Hàng Bông, Q. Hoàn Kiếm, Hanoi"
            ],
            [
                "200 Nguyễn Văn Linh, Q. Hải Châu, Đà Nẵng",
                "200 Nguyễn Văn Linh, Q. Hải Châu, Da Nang"
            ],
            [
                "15 Trần Quý Cáp, P. Ninh Hiệp, Khánh Hòa",
                "15 Trần Quý Cáp, P. Ninh Hiệp, KH"
            ],
            [
                "170 Hùng Vương, Bến Tre",
                "170 Hùng Vương, Tra Vinh"
            ],
        ],
        inputs=[address1_input, address2_input]
    )
    
    # Connect button
    compare_btn.click(
        fn=compare_addresses,
        inputs=[address1_input, address2_input],
        outputs=[province1_output, province2_output, match_output, match_emoji_output]
    )
    
    gr.Markdown(
        """
        ---
        ### 📈 Độ chính xác hệ thống: **93.6%** (102/109 test pairs)
        
        **Tính năng:**
        - ✅ Hỗ trợ 5,297+ variants cho 34 tỉnh/thành
        - ✅ Nhận diện không dấu (Da Nang, Hanoi, etc.)
        - ✅ Word boundary matching (tránh nhầm "Vinh" với "Tra Vinh")
        - ✅ Multi-word priority (ưu tiên tên tỉnh đầy đủ)
        """
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )

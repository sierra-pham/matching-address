"""
Province Comparator Module

Contains the ProvinceComparator class for extracting and comparing 
Vietnamese province names from addresses.
"""

import json
import re


class ProvinceComparator:
    """Class để so sánh địa chỉ dựa trên ground truth"""
    
    def __init__(self, ground_truth_file):
        """
        Khởi tạo với file ground truth
        
        Args:
            ground_truth_file: File tinh_thanh.json
        """
        with open(ground_truth_file, 'r', encoding='utf-8') as f:
            self.ground_truth = json.load(f)
        
        # Tạo reverse mapping: variant -> official name
        self.variant_to_official = {}
        
        for official_name, variants in self.ground_truth.items():
            # Thêm tên chính thức
            self.variant_to_official[official_name] = official_name
            self.variant_to_official[official_name.lower()] = official_name
            
            # Thêm tất cả variants
            for variant in variants:
                self.variant_to_official[variant] = official_name
                self.variant_to_official[variant.lower()] = official_name
        
        # Tạo mapping cho merged provinces
        self.merged_provinces = {}
        for new_province, old_provinces_list in self.ground_truth.items():
            # old_provinces_list là các tỉnh cũ được sáp nhập
            for old_prov in old_provinces_list:
                # Nếu old_prov là tên tỉnh cũ thực sự (không phải abbreviation)
                if any(p in old_prov for p in ['Tỉnh', 'Thành phố', 'TP']):
                    # Map old province -> new province
                    old_official = self.variant_to_official.get(old_prov, old_prov)
                    self.merged_provinces[old_official] = new_province
        
        print(f"✅ Loaded {len(self.ground_truth)} provinces as ground truth")
        print(f"✅ Total variants: {len(self.variant_to_official)}")
    
    def extract_province(self, address):
        """
        Trích xuất tỉnh/thành từ địa chỉ.        
        Args:
            address: Chuỗi địa chỉ
            
        Returns:
            Tên chính thức của tỉnh (theo ground truth) hoặc None
        """
        if not address:
            return None
        
        # Chuyển địa chỉ về lowercase để so sánh
        address_lower = address.lower()
        
        # Thu thập tất cả các match với vị trí của chúng
        candidates = []
        
        for variant, official in self.variant_to_official.items():
            variant_str = variant if isinstance(variant, str) else str(variant)
            variant_lower = variant_str.lower()
            
            # Tìm match
            match = None
            is_word_boundary_match = False
            
            # 1. Thử word boundary match (chính xác hơn)
            pattern = r'(?:^|[\s,;.\-/])(' + re.escape(variant_lower) + r')(?:[\s,;.\-/]|$)'
            regex_match = re.search(pattern, address_lower)
            
            if regex_match:
                match = regex_match
                is_word_boundary_match = True
            # 2. Substring match chỉ cho variants dài >= 4 ký tự
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
                # Lưu candidate với vị trí xuất hiện
                candidates.append({
                    'official': official,
                    'variant': variant_str,
                    'position': match.start(),
                    'is_word_boundary': is_word_boundary_match,
                    'length': len(variant_str)
                })
        
        if not candidates:
            return None
        
        # Sắp xếp theo vị trí (ưu tiên match xuất hiện SAU CÙNG)
        # Nếu cùng vị trí, ưu tiên word boundary, sau đó ưu tiên variant dài hơn
        candidates.sort(key=lambda x: (x['position'], x['is_word_boundary'], x['length']))
        
        # Trả về match CUỐI CÙNG (xuất hiện gần cuối địa chỉ nhất)
        return candidates[-1]['official']
    
    def compare_provinces(self, prov1, prov2):
        """
        So sánh 2 tỉnh, có tính đến sáp nhập
        
        Args:
            prov1: Tên tỉnh 1
            prov2: Tên tỉnh 2
            
        Returns:
            (is_match: bool, reason: str)
        """
        if not prov1 or not prov2:
            return False, "Một trong hai tỉnh không xác định được"
        
        # Exact match
        if prov1 == prov2:
            return True, "Exact match"
        
        # Check if prov1 was merged into prov2
        if prov1 in self.merged_provinces:
            if self.merged_provinces[prov1] == prov2:
                return True, f"Match: {prov1} đã sáp nhập vào {prov2}"
        
        # Check if prov2 was merged into prov1
        if prov2 in self.merged_provinces:
            if self.merged_provinces[prov2] == prov1:
                return True, f"Match: {prov2} đã sáp nhập vào {prov1}"
        
        # Check if both were merged into the same province
        if prov1 in self.merged_provinces and prov2 in self.merged_provinces:
            if self.merged_provinces[prov1] == self.merged_provinces[prov2]:
                new_prov = self.merged_provinces[prov1]
                return True, f"Match: Cả 2 đều sáp nhập vào {new_prov}"
        
        # No match
        return False, f"Mismatch: {prov1} ≠ {prov2}"
    
    def compare_address_pair(self, address1, address2, index):
        """
        So sánh 1 cặp địa chỉ
        
        Args:
            address1: Địa chỉ 1
            address2: Địa chỉ 2
            index: Số thứ tự
            
        Returns:
            Dictionary với kết quả
        """
        prov1 = self.extract_province(address1)
        prov2 = self.extract_province(address2)
        
        is_match, reason = self.compare_provinces(prov1, prov2)
        
        return {
            "index": str(index),
            "address1": address1,
            "address2": address2,
            "province1": prov1 if prov1 else "N/A",
            "province2": prov2 if prov2 else "N/A",
            "match": is_match,
            "reason": reason
        }

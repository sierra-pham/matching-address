"""
Script để so sánh address1 và address2 từ file CSV
Sử dụng tinh_thanh.json làm ground truth
"""

import json
import csv
import re
from vietnamese_utils import normalize_vietnamese


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
        Trích xuất tỉnh/thành từ địa chỉ với Vietnamese normalization
        
        Args:
            address: Chuỗi địa chỉ
            
        Returns:
            Tên chính thức của tỉnh (theo ground truth) hoặc None
        """
        if not address:
            return None
        
        # Chuẩn hóa địa chỉ (xử lý Hoà -> Hòa, etc.)
        address_normalized = normalize_vietnamese(address)
        address_lower = address_normalized.lower()
        
        # Thu thập tất cả các match với scoring
        candidates = []
        
        for variant, official in self.variant_to_official.items():
            variant_str = variant if isinstance(variant, str) else str(variant)
            variant_normalized = normalize_vietnamese(variant_str)
            variant_lower = variant_normalized.lower()
            
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
                # Tính điểm ưu tiên
                score = 0
                score += len(variant_str) * 100  # Độ dài variant
                if is_word_boundary_match:
                    score += 1000  # Word boundary bonus
                position_score = match.start() / len(address_lower) * 50
                score += position_score  # Vị trí trong địa chỉ
                
                # Tiêu chí 4: Multi-word bonus (ưu tiên tên ghép như "Tra Vinh", "Long An")
                if ' ' in variant_str:
                    score += 500  # Bonus cho các variant có nhiều từ
                
                candidates.append({
                    'official': official,
                    'variant': variant_str,
                    'score': score
                })
        
        if not candidates:
            return None
        
        # Sắp xếp và chọn match tốt nhất
        candidates.sort(key=lambda x: x['score'], reverse=True)
        return candidates[0]['official']
    
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


def process_csv(csv_file, ground_truth_file, output_file):
    """
    Xử lý file CSV và so sánh các cặp địa chỉ
    
    Args:
        csv_file: File CSV input
        ground_truth_file: File ground truth
        output_file: File JSON output
    """
    print("🚀 BẮT ĐẦU SO SÁNH ĐỊA CHỈ")
    print("=" * 80)
    
    # Khởi tạo comparator
    comparator = ProvinceComparator(ground_truth_file)
    
    # Đọc CSV
    print(f"\n📖 Đang đọc file CSV: {csv_file}")
    results = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        
        for row in reader:
            # Skip empty rows or rows with MISMATCH/Ambiguity labels
            if not row or len(row) < 3:
                continue
            if len(row) > 3 and row[3] in ['MISMATCH', 'Ambiguity']:
                # Skip rows marked as MISMATCH or Ambiguity in column 4
                continue
            
            index = row[0].strip()
            addr1 = row[1].strip()
            addr2 = row[2].strip()
            
            if addr1 and addr2:
                result = comparator.compare_address_pair(addr1, addr2, index)
                results.append(result)
    
    # Thống kê
    total = len(results)
    matched = sum(1 for r in results if r['match'])
    mismatched = total - matched
    
    print(f"\n📊 THỐNG KÊ:")
    print("=" * 80)
    print(f"Tổng số cặp:     {total}")
    if total > 0:
        print(f"✅ Match:        {matched} ({matched/total*100:.1f}%)")
        print(f"❌ Mismatch:     {mismatched} ({mismatched/total*100:.1f}%)")
    else:
        print("⚠️  Không có dữ liệu để so sánh")
    print("=" * 80)
    
    # Lưu kết quả
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Đã lưu {len(results)} kết quả vào: {output_file}")
    
    # Hiển thị ví dụ
    print("\n📋 VÍ DỤ KẾT QUẢ (5 cặp đầu tiên):")
    print("-" * 80)
    for result in results[:5]:
        status = "✅" if result['match'] else "❌"
        print(f"\n{status} [{result['index']}] {result['reason']}")
        print(f"  Addr1: {result['address1'][:60]}...")
        print(f"  => {result['province1']}")
        print(f"  Addr2: {result['address2'][:60]}...")
        print(f"  => {result['province2']}")
    
    return results


def main():
    """Main function"""
    csv_file = r'C:\Users\Admin\Desktop\Address_Solving\Address_Solving\data\adrdress_wrongmatch.csv'
    ground_truth_file = r'C:\Users\Admin\Desktop\Address_Solving\Address_Solving\data\tinh_thanh.json'
    output_file = r'C:\Users\Admin\Desktop\Address_Solving\Address_Solving\data\address_comparison_output_wrongmatch.json'
    
    results = process_csv(csv_file, ground_truth_file, output_file)
    
    print("\n✅ Hoàn tất!")
    print(f"\n💡 File kết quả: {output_file}")


if __name__ == "__main__":
    main()

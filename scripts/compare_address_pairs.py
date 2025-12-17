"""
Script để so sánh address1 và address2 từ file CSV
Sử dụng tinh_thanh.json làm ground truth
"""

import sys
import os
import json
import csv

# Thêm thư mục gốc vào path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.province_comparator import ProvinceComparator


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
    csv_file = r'C:\Users\Admin\Desktop\Address_Solving\Address_Solving\data\address_match.csv'
    ground_truth_file = r'C:\Users\Admin\Desktop\Address_Solving\address_solving_v2\data\tinh_thanh.json'
    output_file = r'C:\Users\Admin\Desktop\Address_Solving\address_solving_v2\tests\test_data\address_comparison_output.json'
    
    results = process_csv(csv_file, ground_truth_file, output_file)
    
    print("\n✅ Hoàn tất!")
    print(f"\n💡 File kết quả: {output_file}")


if __name__ == "__main__":
    main()

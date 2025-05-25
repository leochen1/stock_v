def merge_txt_files(file1, file2, output_file):
    # 讀取第一個檔案內容
    with open(file1, "r", encoding="utf-8") as f1:
        lines1 = f1.read().splitlines()

    # 讀取第二個檔案內容
    with open(file2, "r", encoding="utf-8") as f2:
        lines2 = f2.read().splitlines()

    # 合併兩個檔案的內容並去除重複項目
    merged_lines = sorted(set(lines1 + lines2))

    # 將合併後的內容寫入輸出檔案
    with open(output_file, "w", encoding="utf-8") as out:
        out.write("\n".join(merged_lines))

    print(f"合併完成，輸出檔案為: {output_file}")


if __name__ == "__main__":
    # 定義檔案路徑
    file1 = "otc_matched_stocks.txt"
    file2 = "twse_matched_stocks.txt"
    output_file = "output.txt"

    # 合併檔案
    merge_txt_files(file1, file2, output_file)
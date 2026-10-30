with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\templates\index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Let's find start and end of the edtech css block
start_str = "    .edtech-dash-wrap {"
end_str = "    /* ===== MODERN SCHOOL PORTAL & EDTECH DESIGN SYSTEM ===== */"

start_pos = content.find(start_str)
end_pos = content.find(end_str)

print("Found start_pos:", start_pos)
print("Found end_pos:", end_pos)
if start_pos != -1 and end_pos != -1:
    print("Block length to replace:", end_pos - start_pos)

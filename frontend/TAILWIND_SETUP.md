# Tailwind CSS Setup

Đã cài đặt và cấu hình Tailwind CSS v3 với shadcn/ui components.

## Để styling hoạt động:

1. **Restart dev server:**
   ```bash
   # Dừng server hiện tại (Ctrl+C)
   # Sau đó chạy lại:
   npm run dev
   ```

2. **Nếu vẫn không thấy styling:**
   - Xóa cache: Xóa thư mục `node_modules/.vite` nếu có
   - Clear browser cache: Hard refresh (Ctrl+Shift+R hoặc Cmd+Shift+R)
   - Kiểm tra console browser để xem có lỗi CSS không

3. **Kiểm tra:**
   - Đảm bảo `index.css` được import trong `main.tsx` ✓
   - Đảm bảo `tailwind.config.js` và `postcss.config.js` tồn tại ✓
   - Đảm bảo Tailwind v3 được cài đặt (không phải v4) ✓

## Components đã được redesign:

- ✅ Sidebar với Tabs, Avatar, Badge
- ✅ ChatArea với Card header
- ✅ MessageList với message bubbles
- ✅ ChatInput với Button và Input components
- ✅ Dark mode được áp dụng mặc định


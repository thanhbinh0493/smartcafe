-- Bộ lọc pandoc cho tài liệu SmartCafe (xuat_docx.py)
--  * Liên kết tới file .md / thư mục / ảnh trong kho: chỉ giữ chữ (bản .docx không mở được đường dẫn tương đối).
--  * Hình đứng riêng một đoạn: chú thích "Hình <chương>.<số>: <mô tả>", đánh số lại theo từng chương (Heading 1).
--  * Đoạn có duy nhất chữ "%%NGAT_TRANG%%": ngắt trang.

local chapter = 0
local figure = 0

function Header(h)
  if h.level == 1 then
    chapter = chapter + 1
    figure = 0
  end
  return h
end

function Link(l)
  local t = l.target
  if t:match("^https?://") or t:match("^mailto:") then
    return l
  end
  return l.content
end

local function caption_of(img)
  return pandoc.utils.stringify(img.caption)
end

-- Kết thúc 1 section: dọc (portrait) hoặc ngang (landscape) – dùng để đặt bảng rộng sang khổ ngang
local MARGIN = '<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1701" w:header="720" w:footer="720" w:gutter="0"/>'
local SECT_DOC = '<w:p><w:pPr><w:sectPr><w:pgSz w:w="11906" w:h="16838"/>' .. MARGIN .. '</w:sectPr></w:pPr></w:p>'
local SECT_NGANG = '<w:p><w:pPr><w:sectPr><w:pgSz w:w="16838" w:h="11906" w:orient="landscape"/>' ..
  '<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134" w:header="720" w:footer="720" w:gutter="0"/></w:sectPr></w:pPr></w:p>'

function Para(p)
  if #p.content == 1 and p.content[1].t == "Str" and p.content[1].text == "%%NGAT_TRANG%%" then
    return pandoc.RawBlock("openxml", '<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
  end
  if #p.content == 1 and p.content[1].t == "Str" and p.content[1].text == "%%NGANG_BAT_DAU%%" then
    return pandoc.RawBlock("openxml", SECT_DOC)       -- phần trước đó: khổ dọc
  end
  if #p.content == 1 and p.content[1].t == "Str" and p.content[1].text == "%%NGANG_KET_THUC%%" then
    return pandoc.RawBlock("openxml", SECT_NGANG)     -- phần vừa xong: khổ ngang
  end
  if #p.content == 1 and p.content[1].t == "Image" then
    local img = p.content[1]
    figure = figure + 1
    local desc = caption_of(img)
    local label = "Hình " .. (chapter > 0 and (chapter .. ".") or "") .. figure
    if desc ~= "" then
      label = label .. ": " .. desc
    end
    img.caption = { pandoc.Str(label) }
    img.title = "fig:"
    return pandoc.Para({ img })
  end
  return p
end

return {
  { Header = Header, Para = Para, Link = Link },
}

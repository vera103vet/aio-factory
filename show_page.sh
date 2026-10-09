#!/bin/bash
# Быстрый просмотр страницы из ячейки
# Использование: ./show_page.sh <номер> [ячейка]

PAGE=${1:-1}
CELL=${2:-07_critic}

FILE="cells/$CELL/page-$PAGE.html"

if [ ! -f "$FILE" ]; then
    echo "❌ Файл не найден: $FILE"
    exit 1
fi

echo " СТРАНИЦА: $PAGE"
echo "📁 ЯЧЕЙКА: $CELL"
echo "📌 ЗАГОЛОВОК:"
grep -oP '<h1[^>]*>\K[^<]+' "$FILE"
echo ""
echo "📝 ТЕКСТ:"
sed 's/<[^>]*>//g' "$FILE" | tr -s ' '
echo ""
echo "📊 РАЗМЕР: $(wc -c < "$FILE") байт, $(wc -w < "$FILE") слов"

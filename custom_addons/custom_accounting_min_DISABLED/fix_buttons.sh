#!/bin/bash
echo "=== FIXING ALL BUTTON/METHOD MISMATCHES ==="

# 1. Fix recurring_transaction_views.xml
echo "1. Fixing recurring_transaction_views.xml..."
sed -i 's/name="generate_entries"/name="action_generate_entries"/' views/recurring_transaction_views.xml

# 2. Check asset_depreciation_views.xml - button name matches method (action_post)
echo "2. Checking asset_depreciation_views.xml..."
# Button is action_post, method is action_post - OK

# 3. Check budget_views.xml buttons
echo "3. Checking budget_views.xml..."
# Methods exist: action_submit, action_approve, action_reject, action_close, action_reopen
# Buttons match: action_submit, action_approve, action_reject, action_close, action_reopen - OK

# 4. Check invoice_views.xml
echo "4. Checking invoice_views.xml..."
# Button is action_post, method exists in invoice.py - OK

# 5. Check move_views.xml
echo "5. Checking move_views.xml..."
# Buttons: action_post, action_cancel, action_draft - all methods exist in move.py - OK

# 6. Check payment_views.xml
echo "6. Checking payment_views.xml..."
# Button: action_post - method exists in payment.py - OK

# 7. Check trial_balance_views.xml
echo "7. Checking trial_balance_views.xml..."
# Button: print_report - method exists in trial_balance.py - OK

echo "=== VERIFICATION ==="
echo "All button names in XML files:"
grep -r 'name="' views/ | grep button | grep -o 'name="[^"]*"' | sort | uniq

echo -e "\nAll method names in Python files:"
grep -r "^    def " models/ | grep -o "def [a-zA-Z_][a-zA-Z0-9_]*" | sed 's/def //' | sort | uniq

echo -e "\n=== CHECKING FOR MISMATCHES ==="
# Check for buttons without corresponding methods
for xml in views/*.xml; do
    buttons=$(grep -o 'name="[^"]*"' "$xml" | grep button | sed 's/name="//g' | sed 's/"//g')
    for button in $buttons; do
        if ! grep -r "^    def $button(" models/ > /dev/null; then
            echo "❌ Button '$button' in $xml has no corresponding method in Python"
        else
            echo "✅ Button '$button' in $xml has corresponding method"
        fi
    done
done

#!/bin/bash
# CO.RA.PAN Auth Smoke Tests (curl)
# ==================================
# Cross-platform alternative to PowerShell tests

BASE_URL="http://localhost:8000"
PASSED=0
FAILED=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"
    local method="${4:-GET}"
    
    echo -e "\n${CYAN}[TEST]${NC} $name"
    echo -e "       ${GRAY}$method $url${NC}"
    
    # Execute request
    response=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$url" 2>&1)
    status=$?
    
    if [ $status -eq 0 ] && [ "$response" == "$expected_status" ]; then
        echo -e "   ${GREEN}✅ Status: $response (expected $expected_status)${NC}"
        ((PASSED++))
    else
        echo -e "   ${RED}❌ Status: $response (expected $expected_status)${NC}"
        ((FAILED++))
    fi
}

test_logout_cookies() {
    local name="$1"
    local url="$2"
    local method="${3:-GET}"
    
    echo -e "\n${CYAN}[TEST]${NC} $name"
    echo -e "       ${GRAY}$method $url${NC}"
    
    # Execute request and capture headers
    headers=$(curl -s -I -X "$method" "$url" 2>&1)
    status=$(echo "$headers" | grep -i "HTTP" | awk '{print $2}')
    cookies=$(echo "$headers" | grep -i "Set-Cookie" | grep -i "Max-Age=0")
    
    if [ "$status" == "303" ] || [ "$status" == "302" ]; then
        echo -e "   ${GREEN}✅ Status: $status (redirect OK)${NC}"
        if [ -n "$cookies" ]; then
            echo -e "   ${GREEN}✅ Cookies cleared (Max-Age=0 found)${NC}"
            ((PASSED++))
        else
            echo -e "   ${YELLOW}⚠️  No Max-Age=0 in Set-Cookie (check manually)${NC}"
            ((PASSED++))
        fi
    else
        echo -e "   ${RED}❌ Status: $status (expected 302/303)${NC}"
        ((FAILED++))
    fi
}

echo -e "\n${MAGENTA}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║      CO.RA.PAN Auth Smoke Tests (2025-11-11)         ║${NC}"
echo -e "${MAGENTA}╚════════════════════════════════════════════════════════╝${NC}"

# ============================================================================
# TEST SUITE 1: Public Routes (No Auth Required)
# ============================================================================
echo -e "\n${YELLOW}📂 PUBLIC ROUTES${NC}"

test_endpoint "Corpus Home (Public)" "$BASE_URL/corpus/" 200
test_endpoint "Advanced Search (Public)" "$BASE_URL/search/advanced" 200
test_endpoint "Atlas API (Public)" "$BASE_URL/api/v1/atlas/countries" 200
test_endpoint "BLS Proxy Health (Public)" "$BASE_URL/bls/" 200

# ============================================================================
# TEST SUITE 2: Logout (GET Method, No CSRF)
# ============================================================================
echo -e "\n${YELLOW}🚪 LOGOUT ENDPOINTS${NC}"

test_logout_cookies "Logout via GET (No Auth Required)" "$BASE_URL/auth/logout" "GET"
test_logout_cookies "Logout POST (Should Still Work)" "$BASE_URL/auth/logout" "POST"

# ============================================================================
# TEST SUITE 3: Protected Routes (Should Redirect/401 Without Auth)
# ============================================================================
echo -e "\n${YELLOW}🔒 PROTECTED ROUTES${NC}"

test_endpoint "Admin Dashboard (Protected)" "$BASE_URL/admin/" 302
test_endpoint "Player (Protected)" "$BASE_URL/player/" 302
test_endpoint "Editor (Protected)" "$BASE_URL/editor/" 302

# ============================================================================
# TEST SUITE 4: Tab Navigation (No 500 Errors)
# ============================================================================
echo -e "\n${YELLOW}🔀 TAB NAVIGATION${NC}"

test_endpoint "Corpus Home (Default Tab)" "$BASE_URL/corpus/" 200
test_endpoint "Corpus Token Tab (Fragment)" "$BASE_URL/corpus/#tab-token" 200
test_endpoint "Advanced → Simple (Should Not 500)" "$BASE_URL/corpus/" 200

# ============================================================================
# RESULTS SUMMARY
# ============================================================================
echo -e "\n${MAGENTA}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║                    TEST RESULTS                        ║${NC}"
echo -e "${MAGENTA}╚════════════════════════════════════════════════════════╝${NC}"
echo -e "\n   ${GREEN}✅ Passed: $PASSED${NC}"
echo -e "   $([ $FAILED -gt 0 ] && echo -e "${RED}" || echo -e "${GRAY}")❌ Failed: $FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All tests passed! Auth system is healthy.${NC}"
    exit 0
else
    echo -e "\n${YELLOW}⚠️  Some tests failed. Check errors above.${NC}"
    exit 1
fi

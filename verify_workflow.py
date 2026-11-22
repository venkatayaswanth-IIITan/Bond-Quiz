import urllib.request
import json

BASE_URL = "http://127.0.0.1:5000"

def test_api():
    print("🚀 Running Live Integration Test against BondQuiz server...")

    # 1. Test Home page
    req = urllib.request.urlopen(f"{BASE_URL}/")
    assert req.status == 200
    home_html = req.read().decode('utf-8')
    assert "How well do your friends" in home_html
    print("✅ 1. Home page loaded successfully.")

    # 2. Test Templates API
    req = urllib.request.urlopen(f"{BASE_URL}/api/templates/best_friend")
    assert req.status == 200
    templates_data = json.loads(req.read().decode('utf-8'))
    assert templates_data['status'] == 'success'
    assert len(templates_data['templates']) >= 5
    print(f"✅ 2. Templates API loaded {len(templates_data['templates'])} sample questions.")

    # 3. Create a brand new quiz via POST /api/quizzes
    payload = {
        'creator_name': 'E2E_Tester',
        'title': 'Can You Beat The Ultimate Test?',
        'description': 'Automated end-to-end verification quiz.',
        'category': 'best_friend',
        'theme': 'sunset_glow',
        'avatar': 'rocket',
        'questions': [
            {
                'question_text': 'What is my favorite animal?',
                'options': ['Panda 🐼', 'Wolf 🐺', 'Cat 🐱', 'Otter 🦦'],
                'correct_index': 0
            },
            {
                'question_text': 'What superpower would I choose?',
                'options': ['Invisibility', 'Flight', 'Time Travel', 'Teleportation'],
                'correct_index': 3
            },
            {
                'question_text': 'Morning or Night person?',
                'options': ['Early Morning 🌅', 'Night Owl 🦉', 'Midday Sleeper 😴', 'Depends on coffee ☕'],
                'correct_index': 1
            }
        ]
    }
    create_req = urllib.request.Request(
        f"{BASE_URL}/api/quizzes",
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    res = urllib.request.urlopen(create_req)
    assert res.status == 201
    created = json.loads(res.read().decode('utf-8'))
    public_id = created['public_id']
    creator_token = created['creator_token']
    print(f"✅ 3. Created Quiz (Public ID: {public_id}, Token: {creator_token[:10]}...)")

    # 4. Fetch public quiz API and verify NO is_correct is leaked
    quiz_res = urllib.request.urlopen(f"{BASE_URL}/api/quizzes/{public_id}")
    assert quiz_res.status == 200
    quiz_data = json.loads(quiz_res.read().decode('utf-8'))['quiz']
    for q in quiz_data['questions']:
        for opt in q['options']:
            assert 'is_correct' not in opt, "SECURITY BREACH: is_correct found in public options!"
    print("✅ 4. Verified public quiz API: 0 answer leaks detected.")

    # 5. Start attempt for participant "Chris"
    start_req = urllib.request.Request(
        f"{BASE_URL}/api/quizzes/{public_id}/start",
        data=json.dumps({'participant_name': 'Chris'}).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    start_res = urllib.request.urlopen(start_req)
    assert start_res.status == 200
    start_data = json.loads(start_res.read().decode('utf-8'))
    attempt_token = start_data['attempt_token']
    print(f"✅ 5. Started attempt for Chris (Attempt Token: {attempt_token[:10]}...)")

    # 6. Submit Chris's answers
    # Get option IDs from public quiz
    q1 = quiz_data['questions'][0]
    q2 = quiz_data['questions'][1]
    q3 = quiz_data['questions'][2]

    # Chris picks Option 0 (Correct), Option 3 (Correct), Option 0 (Incorrect) -> Expected 2/3 (66.7%)
    submit_payload = {
        'attempt_token': attempt_token,
        'answers': {
            q1['id']: q1['options'][0]['id'],
            q2['id']: q2['options'][3]['id'],
            q3['id']: q3['options'][0]['id']
        }
    }
    submit_req = urllib.request.Request(
        f"{BASE_URL}/api/quizzes/{public_id}/submit",
        data=json.dumps(submit_payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    submit_res = urllib.request.urlopen(submit_req)
    assert submit_res.status == 200
    sub_data = json.loads(submit_res.read().decode('utf-8'))
    assert sub_data['result']['score'] == 2
    assert sub_data['result']['total_questions'] == 3
    assert sub_data['result']['percentage'] == 66.7
    print(f"✅ 6. Submitted answers. Score: {sub_data['result']['score']}/3 ({sub_data['result']['percentage']}%)")

    # 7. Check Public Leaderboard HTML and API
    lb_res = urllib.request.urlopen(f"{BASE_URL}/api/quizzes/{public_id}/leaderboard")
    assert lb_res.status == 200
    lb_data = json.loads(lb_res.read().decode('utf-8'))
    assert len(lb_data['leaderboard']) == 1
    assert lb_data['leaderboard'][0]['participant_name'] == 'Chris'
    assert lb_data['leaderboard'][0]['trophy'] == '🥇'
    print("✅ 7. Public leaderboard verified: Chris is #1 Gold with 🥇.")

    # 8. Check Creator Dashboard API with Token
    dash_req = urllib.request.Request(
        f"{BASE_URL}/api/creator/dashboard/{public_id}",
        headers={'X-Creator-Token': creator_token}
    )
    dash_res = urllib.request.urlopen(dash_req)
    assert dash_res.status == 200
    dash_data = json.loads(dash_res.read().decode('utf-8'))
    assert dash_data['stats']['total_participants'] == 1
    assert dash_data['stats']['average_score'] == 2.0
    print("✅ 8. Creator Dashboard verified with secure token.")

    # 9. Verify Unauthorized Creator Access is blocked
    try:
        unauth_req = urllib.request.Request(f"{BASE_URL}/api/creator/dashboard/{public_id}")
        urllib.request.urlopen(unauth_req)
        assert False, "Should have thrown 401"
    except urllib.error.HTTPError as e:
        assert e.code == 401
    print("✅ 9. Unauthorized creator access blocked with HTTP 401.")

    # 10. Pause Quiz & verify attempt blocking
    pause_req = urllib.request.Request(
        f"{BASE_URL}/api/creator/quizzes/{public_id}",
        data=json.dumps({'is_active': False}).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'X-Creator-Token': creator_token},
        method='PUT'
    )
    pause_res = urllib.request.urlopen(pause_req)
    assert pause_res.status == 200

    try:
        blocked_req = urllib.request.Request(
            f"{BASE_URL}/api/quizzes/{public_id}/start",
            data=json.dumps({'participant_name': 'LateUser'}).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        urllib.request.urlopen(blocked_req)
        assert False, "Should have thrown 403"
    except urllib.error.HTTPError as e:
        assert e.code == 403
    print("✅ 10. Closed quiz correctly rejected new participants with HTTP 403.")

    # 11. Cleanup test quiz
    del_req = urllib.request.Request(
        f"{BASE_URL}/api/creator/quizzes/{public_id}",
        headers={'X-Creator-Token': creator_token},
        method='DELETE'
    )
    del_res = urllib.request.urlopen(del_req)
    assert del_res.status == 200
    print("✅ 11. Deleted test quiz and cascaded all records.")

    # 12. Verify Google Site Verification Tag & SEO Metadata
    req_home = urllib.request.urlopen(f"{BASE_URL}/")
    home_content = req_home.read().decode('utf-8')
    assert 'name="google-site-verification" content="FkGajWtj6EQhtar92w0fYD53RZLtyt6i_yiyrivGE3M"' in home_content
    assert 'rel="canonical" href="https://bond-quiz-1.onrender.com/"' in home_content
    assert 'name="robots" content="index, follow"' in home_content
    assert 'property="og:site_name" content="BondQuiz"' in home_content
    assert '"@type": "WebApplication"' in home_content
    print("✅ 12. Verified Google Search Console tag, canonical URL, and SEO structured data.")

    # 13. Verify robots.txt
    req_robots = urllib.request.urlopen(f"{BASE_URL}/robots.txt")
    assert req_robots.status == 200
    assert 'text/plain' in req_robots.headers.get('Content-Type')
    robots_data = req_robots.read().decode('utf-8')
    assert 'User-agent: *' in robots_data
    assert 'Disallow: /creator/' in robots_data
    assert 'Disallow: /api/' in robots_data
    assert 'Sitemap: https://bond-quiz-1.onrender.com/sitemap.xml' in robots_data
    print("✅ 13. Verified /robots.txt with correct crawler rules and sitemap pointer.")

    # 14. Verify sitemap.xml
    req_sitemap = urllib.request.urlopen(f"{BASE_URL}/sitemap.xml")
    assert req_sitemap.status == 200
    assert 'xml' in req_sitemap.headers.get('Content-Type')
    sitemap_data = req_sitemap.read().decode('utf-8')
    assert '<?xml version="1.0" encoding="UTF-8"?>' in sitemap_data
    assert '<urlset' in sitemap_data
    assert '<loc>https://bond-quiz-1.onrender.com/</loc>' in sitemap_data
    assert '<loc>https://bond-quiz-1.onrender.com/create</loc>' in sitemap_data
    print("✅ 14. Verified /sitemap.xml returns valid XML format.")

    print("\n🎉 ALL 14 END-TO-END WORKFLOW CHECKS PASSED PERFECTLY!")

if __name__ == '__main__':
    test_api()

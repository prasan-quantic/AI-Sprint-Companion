# Presentation Checklist

## AI Sprint Companion - Capstone Presentation

**Version:** 1.1.0  
**Date:** February 8, 2026

### Pre-Presentation Setup

#### Technical Setup
- [ ] Application is deployed on Render.com and accessible
- [ ] Local backup is running (in case of deployment issues)
- [ ] AI provider is configured and working (mock mode is fine)
- [ ] Jira integration is configured (optional but recommended)
- [ ] All demo data is prepared (see `samples/` folder)
- [ ] Browser tabs are pre-loaded:
  - [ ] Home page (`/`)
  - [ ] Standup page (`/standup`)
  - [ ] Stories page (`/stories`)
  - [ ] Tasks page (`/tasks`)
  - [ ] Jira page (`/jira`)
  - [ ] API docs (`/docs`)
- [ ] Screen resolution is appropriate for sharing
- [ ] MCP tests have passed (`run_mcp_test.bat`)

#### Materials Ready
- [ ] Slide deck (if applicable)
- [ ] Demo script reviewed (see `docs/DEMO_SCRIPT.md`)
- [ ] Backup screenshots prepared
- [ ] Repository URL ready to share
- [ ] Deployed app URL ready to share
- [ ] Sample data files ready

#### Environment Check
- [ ] Stable internet connection
- [ ] Microphone tested
- [ ] Camera tested (if video presentation)
- [ ] Screen sharing tested
- [ ] Backup device available

---

### Presentation Outline

#### 1. Introduction (2 min)
- [ ] Introduce yourself
- [ ] State the project name: "AI Sprint Companion"
- [ ] Explain the problem being solved
- [ ] Brief overview of the solution

#### 2. Problem Statement (2 min)
- [ ] Describe pain points in Scrum processes
  - [ ] Time-consuming standup note-taking
  - [ ] Inconsistent user story formatting
  - [ ] Manual task breakdown process
  - [ ] Disconnected tools (meetings → backlog)
- [ ] Explain the target audience (Scrum teams)

#### 3. Solution Overview (3 min)
- [ ] Explain the five core features:
  - [ ] Standup summary generation
  - [ ] User story generation
  - [ ] Sprint task suggestions
  - [ ] Jira ticket creation
  - [ ] MCP protocol for AI agents
- [ ] Mention technology stack

#### 4. Live Demo (10-12 min)
- [ ] Home page tour
- [ ] Standup Summary feature
  - [ ] Enter sample standup data
  - [ ] Show file upload option
  - [ ] Generate summary
  - [ ] Highlight blockers and action items
  - [ ] Show suggested tasks and stories
- [ ] User Story Generator
  - [ ] Enter meeting notes
  - [ ] Generate user stories
  - [ ] Show acceptance criteria and story points
- [ ] Sprint Task Suggestions
  - [ ] Enter user stories
  - [ ] Set team capacity
  - [ ] Generate tasks with estimates
  - [ ] Show recommendations
- [ ] Jira Integration
  - [ ] Show Jira configuration status
  - [ ] Create a ticket from generated story
  - [ ] Show ticket in Jira (if configured)
- [ ] API Documentation
  - [ ] Show Swagger UI
  - [ ] Demonstrate an API call
- [ ] MCP Protocol (optional)
  - [ ] Show MCP test results
  - [ ] Explain AI agent integration

#### 5. Architecture & Technology (3 min)
- [ ] Show architecture diagram
- [ ] Explain key technologies:
  - [ ] Python 3.13 + FastAPI
  - [ ] OpenAI GPT-4o-mini
  - [ ] HTMX for dynamic UI
  - [ ] Jira Cloud API
  - [ ] MCP Protocol
- [ ] Mention deployment on Render.com

#### 6. Testing & Quality (2 min)
- [ ] Mention comprehensive test suite (11 test files)
- [ ] Show MCP agent test results
- [ ] Explain CI/CD pipeline
- [ ] Mention code quality tools (Ruff, type hints)

#### 7. Conclusion (2 min)
- [ ] Summarize key achievements:
  - [ ] 13 user stories completed
  - [ ] 72 story points delivered
  - [ ] Full test coverage
  - [ ] Production-ready deployment
- [ ] Mention future enhancements
- [ ] Thank the audience

#### 8. Q&A (5 min)
- [ ] Prepare for common questions:
  - [ ] AI accuracy and reliability
  - [ ] Using different AI providers
  - [ ] Jira vs other tools
  - [ ] Deployment options
  - [ ] MCP protocol use cases

---

### Demo Data Prepared

#### Standup Sample
```
Alice: Completed user authentication API | Working on dashboard components | Waiting for design mockups
Bob: Fixed critical login bug | Code review for Alice's PR | None
Carol: Sprint planning preparation | Starting payment integration | Need API credentials from finance team
```

#### Meeting Notes Sample
```
In today's stakeholder meeting, we discussed:
1. Users need password reset via email with 24-hour expiration
2. Admin team wants to view/manage all user accounts
3. Add two-factor authentication option
4. Dashboard needs recent activity widget
```

#### User Stories Sample
```
As a user, I want to reset my password via email so that I can regain access to my account
As an admin, I want to view all user accounts so that I can maintain platform security
As a user, I want to enable two-factor authentication so that my account is more secure
```

---

### Backup Plans

#### If Render.com is Down
1. Run locally: `run.bat` or `python -m uvicorn app.main:app --reload`
2. Use `http://localhost:8000`

#### If AI API is Down
1. Set `AI_PROVIDER=mock` in environment
2. Mock responses will still demonstrate the flow

#### If Jira is Not Configured
1. Skip Jira demo section
2. Explain the feature conceptually
3. Show API documentation for Jira endpoints

#### If Live Demo Fails
1. Use pre-recorded video backup
2. Show screenshots
3. Demonstrate API via curl/Postman

---

### Post-Presentation

- [ ] Share deployed app URL
- [ ] Share GitHub repository URL
- [ ] Share documentation links
- [ ] Collect feedback
- [ ] Answer follow-up questions

---

### Quick Reference

| Resource | URL |
|----------|-----|
| Deployed App | https://ai-sprint-companion.onrender.com |
| API Docs | https://ai-sprint-companion.onrender.com/docs |
| GitHub Repo | (your repository URL) |
| Design Document | `docs/DESIGN_DOCUMENT.md` |
| Demo Script | `docs/DEMO_SCRIPT.md` |

---

### Timing Guide

| Section | Duration | Cumulative |
|---------|----------|------------|
| Introduction | 2 min | 2 min |
| Problem Statement | 2 min | 4 min |
| Solution Overview | 3 min | 7 min |
| Live Demo | 10-12 min | 17-19 min |
| Architecture | 3 min | 20-22 min |
| Testing | 2 min | 22-24 min |
| Conclusion | 2 min | 24-26 min |
| Q&A | 5 min | 29-31 min |

**Total: ~30 minutes**

---

### Confidence Boosters

✨ You built a complete, working application!

✨ Your code follows best practices!

✨ You have comprehensive tests!

✨ Your documentation is thorough!

✨ You're prepared - you've got this! 💪

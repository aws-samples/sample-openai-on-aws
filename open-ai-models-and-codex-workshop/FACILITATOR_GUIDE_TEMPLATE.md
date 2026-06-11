# Facilitator Guide: [Your Workshop Title]

> **⚠️ Authoring Notes — DELETE this entire block before publishing. If you don't, facilitators will see it in the rendered guide.**
>
> **File setup:**
> - Name this file `FACILITATOR_GUIDE.md` and place it at the root of your workshop repository. The build process parses it and stores the content for rendering in Workshop Studio.
> - **Max length: 100,000 characters.** Going over this limit will fail the build. Cut sections you don't need.
> - **Images aren't supported.** Don't use `![image](...)` syntax; it won't render. Link to external resources or describe things in text instead.
>
> **Markdown support:**
> - Standard markdown (headers, tables, bold, lists, links) all works.
> - Workshop Studio directives such as `:::alert{type="warning"}` and `:::expand{header="..."}` also work. You'll see examples in the Troubleshooting section below. Check the [WS content authoring docs](https://catalog.workshops.aws/docs/en-US/detailed-documentation/directives) for the full directive list.
>
> **Section guidance:**
> - Labels such as `REQUIRED` and `SUGGESTED` are authoring guidance only. The build process won't enforce section presence. They're here to help you prioritize.
> - **Keep the `##` section headers as-is** (for example, keep "Troubleshooting" rather than renaming it "Known Issues"). Workshop Studio analytics reads these headers to measure guide composition across the catalog.
> - Start with **Workshop Overview**, **Troubleshooting**, and **Resources**. Those three do the most for facilitators.
>
> **Previewing:**
> - After you build, open **Build Details** in Workshop Studio to see a rendered preview of your guide before publishing.
>
> **Checklist** (use while writing, then delete):
> - [ ] Workshop Overview filled in
> - [ ] Prerequisites and service quotas documented
> - [ ] Agenda with realistic timing
> - [ ] Delivery tips written
> - [ ] Troubleshooting section populated (even for brand-new workshops, run through it once and note what comes up)
> - [ ] Resources linked
>
> For full authoring guidance, see: [Workshop Studio Facilitator Guide Documentation](https://catalog.workshops.aws/docs/en-US/create-a-workshop/authoring-a-workshop/facilitator-guide)


---

## Workshop Overview

REQUIRED: What the workshop teaches and who it's for.

**What Participants Will Learn:** [Your Workshop Name] teaches participants how to [primary skill/outcome]. By the end, they'll be able to [specific capability 1] and [specific capability 2].

**Learning Objectives:**
- [Objective 1, e.g., "Deploy a serverless application using AWS Lambda and API Gateway"]
- [Objective 2, e.g., "Configure CloudWatch monitoring and alarms for production workloads"]

**Target Audience:** [e.g., "Solutions Architects with 6+ months of AWS experience"]


---

## Prerequisites

REQUIRED: What facilitators and participants need before the event.

### Facilitator Preparation

- Walk through the full workshop yourself (budget [X] minutes) to understand the flow and catch issues early
- Test by launching a test event in Workshop Studio. Make sure all resources deploy correctly.
- Grab your presentation slides from [link] if available
- Read the Troubleshooting section below so you're ready for common questions

### Service Requirements & Quotas

Document the AWS quotas and limits facilitators should know about **before** the event.

- **Services used:** [e.g., "AWS Lambda, Amazon S3, Amazon DynamoDB, Amazon API Gateway"]
- **Quota requirements:** [e.g., "Default Lambda concurrent execution quota (1,000) covers up to 40 participants"]
- **Large events:** For 200+ participants, contact [X] service team at [support channel] at least a week in advance to ensure there are no capacity concerns
- **Account setup:** [e.g., "Nothing extra needed. Workshop Studio pre-configures the required IAM roles."]

### Participant Prerequisites

- [Skill 1, e.g., "Basic AWS console navigation"]
- [Skill 2, e.g., "Familiarity with VPCs and subnets"]
- [Tooling, e.g., "Modern web browser (Chrome, Firefox, Edge)"]

---

## Recommended Agenda

SUGGESTED: Adjust the rows below to match your actual workshop length (1 hour, 3 hours, full day, whatever it is).

### Standard 3-Hour Format

| Time | Duration | Activity | Key Focus & Tips |
|------|----------|----------|------------------|
| 0:00–0:15 | 15 min | Welcome & Setup | Introduce objectives, confirm everyone can access Workshop Studio. Set expectations for breaks and Q&A. |
| 0:15–0:45 | 30 min | Module 1: [Name] | **Focus:** [What to emphasize] **Outcome:** [What participants complete] |
| 0:45–1:15 | 30 min | Module 2: [Name] | **Focus:** [What to emphasize] **Outcome:** [What participants complete] |
| 1:15–1:30 | 15 min | Break | Encourage participants to stay nearby |
| 1:30–2:00 | 30 min | Module 3: [Name] | **Focus:** [What to emphasize] |
| 2:00–2:30 | 30 min | Module 4: [Name] | **Focus:** [What to emphasize] |
| 2:30–2:50 | 20 min | Optional Challenge | For early finishers: [Stretch goal] |
| 2:50–3:00 | 10 min | Wrap-up & Next Steps | Review key learnings, share resources |

**Pacing tips:**
- Module [X] usually runs 5–10 minutes long. Build in buffer.
- With 20+ participants, keep per-module Q&A short and use breakout support.
- [Any other timing advice from your experience]

---

## Delivery Tips

SUGGESTED: How to actually run the event once it starts.

### Setup & Environment

- Start provisioning accounts [X] minutes early. Setup takes time.
- Have a backup plan (e.g., keeping one fully-deployed environment around for demos if something breaks)
- Test screen sharing and audio before participants join

**Regional notes:**
- Good regions: [e.g., "us-east-1, us-west-2, eu-west-1"] for broad service availability
- Regions to avoid: [e.g., "Limited instance types in ap-south-1"]
- Cost per participant: roughly [e.g., "$1–2 USD"], cleanup is automatic

### Facilitation Strategies

**What works well:**
- [e.g., "Ask participants about their use cases during intros. It helps you customize examples on the fly."]
- [e.g., "Explain the 'why' before the 'how'. Context helps people retain more."]

**Common mistakes:**
- [e.g., "Don't skip the architecture overview. Participants need that context before diving in."]
- [e.g., "Don't assume everyone is on the same step. Check progress often."]

**Mixed skill levels:**
- Beginners: [e.g., "Pair them with experienced participants during hands-on sections"]
- Advanced: [e.g., "Point them to optional challenges"]
- Large groups (20+): [e.g., "Use breakout rooms so everyone gets support"]

---

## Troubleshooting

REQUIRED: This section prevents delivery failures. It's worth spending real time on.

For brand-new workshops where you haven't hit issues yet, run through the workshop yourself once and write down anything that trips you up. That first pass catches most of the problems facilitators will face.

### Top Issues

#### 1. "AccessDenied when trying to [specific action]"

:::alert{type="warning"}
This is the most common issue across workshops. Check credentials first.
:::

**Cause:** [Why it happens, e.g., "Participant is using their personal AWS account instead of Workshop Studio credentials"]

**Fix:**
- Confirm the participant is using Workshop Studio credentials, not their personal account
- Have them refresh the Workshop Studio tab for new session credentials
- If it's still failing, check that the IAM role has [PolicyName] attached in the console

#### 2. "[Specific error from your workshop]"

**Cause:** [Why it happens]

**Fix:** [Step-by-step solution]

#### 3. "My [resource] isn't showing up"

**Cause:** The resource may still be creating. This can take 2–3 minutes.

**Fix:**
- Wait 2–3 minutes and refresh the console
- Check the CloudFormation stack status (should say "CREATE_COMPLETE")
- Confirm the participant is in the correct region: [your workshop's region]

### Module-Specific Issues

**Module 1: [Name]**
- **Issue:** [Description]
- **Solution:** [How to fix]

**Module 2: [Name]**
- **Issue:** [Description]
- **Solution:** [How to fix]

### Service Limits & Quotas

:::expand{header="Service quota issues during delivery"}
- **"Error: Service limit exceeded"**: Rare, but it can happen for very large events (100+ participants). Contact service team support before the event to discuss limits and capacity.
- **"Everything is slow / timing out"**: Sometimes happens during peak hours. Wait 2–3 minutes for resources to come up, or plan future events in a less busy region.
:::

### When Nothing Works

If you hit something that isn't listed here:
1. Check Workshop Studio event logs for detailed error messages
2. Ask the Workshop Studio Atlas Agent from the UI
3. Ask in #workshop-studio-interest (Slack)
4. **Add it to this guide after you fix it.** The next facilitator will appreciate it.

---

## Resources

REQUIRED: Link everything facilitators and participants need.

### For Facilitators

- **Slides:** [Link, e.g., a Quip doc, WorkDocs folder, or S3 URL]
- **Demo recording:** [Link, if you have one]
- **Support channel:** [e.g., "Workshop Studio Atlas Agent from the UI, or #workshop-studio-interest on Slack"]
- **Source code:** [Link to the repo or code samples]

### For Participants (share after the event)

- **AWS documentation:** [Service docs relevant to the workshop]
- **Blog posts:** [Tutorials or deeper dives]
- **What to do next:** [Follow-on workshops or learning paths]
- **Reference architecture:** [Diagrams or architecture patterns]

---

## Post-Event Actions

REQUIRED: Terminate the event in Workshop Studio. Cleanup is automatic, no manual steps needed.

OPTIONAL:

- Collect feedback: [your method]
- Send participants the links from the Resources section above
- **Update this guide** if you found new issues or better approaches
- Report content bugs to [contact method]

---

## Additional Notes

OPTIONAL:

- [Anything unusual about this workshop, e.g., "Uses preview features, behavior may change"]
- [Security or compliance notes if relevant]

---

## Need Help?

- **Improve this guide:** Found a problem or have a suggestion? [Contact method or contribution process]
- **Workshop Studio support:** Ask the Workshop Studio Atlas Agent from the UI, or #workshop-studio-interest (Slack)
- **Authoring docs:** [Workshop Studio Facilitator Guide Documentation](https://catalog.workshops.aws/docs/en-US/create-a-workshop/authoring-a-workshop/facilitator-guide)

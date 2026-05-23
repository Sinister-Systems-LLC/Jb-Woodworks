import re

with open('careers.html', 'r', encoding='utf-8') as f:
    s = f.read()

# Step 1: Remove the entire OPEN POSITIONS section
pat = re.compile(r'  <!-- OPEN POSITIONS .*?</section>\n\n', re.DOTALL)
m = pat.search(s)
if m:
    intro = '''  <!-- INTRO PITCH -->
  <section style="padding: 50px 0 30px;">
    <div class="container" style="max-width: 880px;">
      <div class="testimonial-eyebrow">One application &middot; every role</div>
      <h2 class="section-headline" style="margin-bottom: 18px;">Tell us what you can do.<br/><em>We will find the shifts that fit.</em></h2>
      <p style="color: var(--text-2); font-size: 1.06rem; line-height: 1.65; margin: 0 0 14px;">
        We do not post one role at a time. Tell us about your skills, your certifications, and your experience &mdash; we categorize you across the bench (stagehand, rigger, technician, lift operator, Crew Lead, technical director, office) and route you to the shifts that match. One application, every fitting role.
      </p>
      <p style="color: var(--text-3); font-size: 0.92rem; margin: 0;">W-4 employment. Workers comp + $2M GL + ACA-compliant benefits. Recerts paid (ETCP, SPRAT, OSHA, lift). Five-business-day reply.</p>
    </div>
  </section>

'''
    s = s[:m.start()] + intro + s[m.end():]
    print('Removed OPEN POSITIONS section')
else:
    print('OPEN POSITIONS section NOT found')

# Step 2: Replace the existing form with expanded version
form_pat = re.compile(r'<form id="applyForm".*?</form>', re.DOTALL)
m2 = form_pat.search(s)
if m2:
    NEW_FORM = """<form id="applyForm" class="apply-form-wrap" novalidate>
          <div class="apply-stamp">
            <span class="apply-stamp-k">FORM</span>
            <span class="apply-stamp-v">SMPL-CREW-APP</span>
          </div>

          <fieldset class="cs-block">
            <legend class="cs-legend">A &middot; You</legend>
            <div class="cs-grid">
              <label class="cs-field"><span class="cs-field-k">First name <em>*</em></span><input type="text" name="first" required /></label>
              <label class="cs-field"><span class="cs-field-k">Last name <em>*</em></span><input type="text" name="last" required /></label>
              <label class="cs-field"><span class="cs-field-k">Email <em>*</em></span><input type="email" name="email" required placeholder="you@example.com" /></label>
              <label class="cs-field"><span class="cs-field-k">Phone <em>*</em></span><input type="tel" name="phone" required placeholder="(555) 555-5555" /></label>
            </div>
          </fieldset>

          <fieldset class="cs-block">
            <legend class="cs-legend">B &middot; Home base</legend>
            <div class="cs-grid">
              <label class="cs-field"><span class="cs-field-k">City <em>*</em></span><input type="text" name="city" required /></label>
              <label class="cs-field">
                <span class="cs-field-k">State <em>*</em></span>
                <select name="state" required>
                  <option value="" disabled selected>&mdash;</option>
                  <option>AL</option><option>AK</option><option>AZ</option><option>AR</option><option>CA</option><option>CO</option><option>CT</option><option>DE</option><option>FL</option><option>GA</option><option>HI</option><option>ID</option><option>IL</option><option>IN</option><option>IA</option><option>KS</option><option>KY</option><option>LA</option><option>ME</option><option>MD</option><option>MA</option><option>MI</option><option>MN</option><option>MS</option><option>MO</option><option>MT</option><option>NE</option><option>NV</option><option>NH</option><option>NJ</option><option>NM</option><option>NY</option><option>NC</option><option>ND</option><option>OH</option><option>OK</option><option>OR</option><option>PA</option><option>RI</option><option>SC</option><option>SD</option><option>TN</option><option>TX</option><option>UT</option><option>VT</option><option>VA</option><option>WA</option><option>WV</option><option>WI</option><option>WY</option><option>DC</option>
                </select>
              </label>
              <label class="cs-field"><span class="cs-field-k">Willing to travel?</span>
                <select name="travel">
                  <option>Yes &mdash; anywhere in the US</option>
                  <option>Yes &mdash; within my home region</option>
                  <option>Local only</option>
                </select>
              </label>
              <label class="cs-field"><span class="cs-field-k">Years of pro experience</span><input type="number" name="yrs" min="0" max="60" placeholder="0" /></label>
            </div>
          </fieldset>

          <fieldset class="cs-block">
            <legend class="cs-legend">C &middot; What can you do? <em>*</em></legend>
            <p class="cs-help">Check every role you can run a shift in. We use this to route you to fitting calls.</p>
            <div class="expertise-grid">
              <label class="cs-check"><input type="checkbox" name="exp" value="sh_general"/> <span>Stagehand &mdash; general</span></label>
              <label class="cs-check"><input type="checkbox" name="exp" value="sh_audio"/> <span>Stagehand &mdash; audio</span></label>
              <label class="cs-check"><input type="checkbox" name="exp" value="sh_light"/> <span>Stagehand &mdash; lighting</span></label>
              <label class="cs-check"><input type="checkbox" name="exp" value="sh_video"/> <span>Stagehand &mdash; video</span></label>
              <label class="cs-check"><input type="checkbox" name="exp" value="sh_carp"/> <span>Stagehand &mdash; carpentry / scenic</span></label>
              <label class="cs-check"><input type="checkbox" name="exp" value="sh_deck"/> <span>Stagehand &mdash; decking</span></label>
              <label class="cs-check"><input type="checkbox" name="exp" value="rigging_lead"/> <span>Lead Rigger</span></label>
              <label class="cs-check"><input type="checkbox" name="exp" value="rigging_up"/> <span>Up-Rigger</span></label>
              <label class="cs-check"><input type="checkbox" name="exp" value="rigging_ground"/> <span>Ground Rigger</span></label>
              <label class="cs-check"><input type="checkbox" name="exp" value="t_audio"/> <span>Audio Technician / Engineer</span></label>
              <label class="cs-check"><input type="checkbox" name="exp" value="t_light"/> <span>Lighting Tech / Programmer</span></label>
              <label class="cs-check"><input type="checkbox" name="exp" value="t_video"/> <span>Video Tech / TD</span></label>
              <label class="cs-check"><input type="checkbox" name="exp" value="t_virtual"/> <span>Virtual / Hybrid Streaming Tech</span></label>
              <label class="cs-check"><input type="checkbox" name="exp" value="forklift"/> <span>Forklift Operator</span></label>
              <label class="cs-check"><input type="checkbox" name="exp" value="boomlift"/> <span>Boom / Scissor Lift Operator</span></label>
              <label class="cs-check"><input type="checkbox" name="exp" value="camera"/> <span>Camera Operator</span></label>
              <label class="cs-check"><input type="checkbox" name="exp" value="spotlight"/> <span>Spotlight / Follow-Spot Operator</span></label>
              <label class="cs-check"><input type="checkbox" name="exp" value="crewlead"/> <span>Crew Lead</span></label>
              <label class="cs-check"><input type="checkbox" name="exp" value="stagemgr"/> <span>Stage Manager</span></label>
              <label class="cs-check"><input type="checkbox" name="exp" value="td"/> <span>Technical Director</span></label>
              <label class="cs-check"><input type="checkbox" name="exp" value="warehouse"/> <span>Warehouse / Truck Pack</span></label>
              <label class="cs-check"><input type="checkbox" name="exp" value="office"/> <span>Office &mdash; Coordinator / Sales / Ops</span></label>
            </div>
          </fieldset>

          <fieldset class="cs-block">
            <legend class="cs-legend">D &middot; Skill level</legend>
            <p class="cs-help">Self-assessed. We do not penalize honest answers &mdash; we match you to the right shift.</p>
            <div class="cs-grid">
              <label class="cs-field">
                <span class="cs-field-k">Primary skill area</span>
                <input type="text" name="primary_skill" placeholder="e.g. Audio engineer, Lead Rigger, Stagehand" />
              </label>
              <label class="cs-field">
                <span class="cs-field-k">Years in primary area</span>
                <input type="number" name="primary_years" min="0" max="60" placeholder="0" />
              </label>
              <label class="cs-field">
                <span class="cs-field-k">Self-rating &mdash; primary</span>
                <select name="primary_level">
                  <option>Rookie / first calls</option>
                  <option>Working pro</option>
                  <option>Senior pro</option>
                  <option>Lead / mentor</option>
                </select>
              </label>
              <label class="cs-field">
                <span class="cs-field-k">Largest show you have crewed</span>
                <input type="text" name="biggest_show" placeholder="Venue + scale, e.g. AT&amp;T Stadium NFL halftime" />
              </label>
            </div>
          </fieldset>

          <fieldset class="cs-block">
            <legend class="cs-legend">E &middot; Certifications</legend>
            <p class="cs-help">Check every current cert. We pay for renewals once you are on the bench.</p>
            <div class="expertise-grid">
              <label class="cs-check"><input type="checkbox" name="cert" value="etcp_r"/> <span>ETCP-Rigger</span></label>
              <label class="cs-check"><input type="checkbox" name="cert" value="etcp_e"/> <span>ETCP-Electrician</span></label>
              <label class="cs-check"><input type="checkbox" name="cert" value="sprat_1"/> <span>SPRAT Level 1</span></label>
              <label class="cs-check"><input type="checkbox" name="cert" value="sprat_2"/> <span>SPRAT Level 2/3</span></label>
              <label class="cs-check"><input type="checkbox" name="cert" value="osha10"/> <span>OSHA-10</span></label>
              <label class="cs-check"><input type="checkbox" name="cert" value="osha30"/> <span>OSHA-30</span></label>
              <label class="cs-check"><input type="checkbox" name="cert" value="osha_fall"/> <span>OSHA Fall Protection</span></label>
              <label class="cs-check"><input type="checkbox" name="cert" value="pit"/> <span>OSHA PIT (Forklift)</span></label>
              <label class="cs-check"><input type="checkbox" name="cert" value="boom"/> <span>Boom / Scissor Lift</span></label>
              <label class="cs-check"><input type="checkbox" name="cert" value="cdl"/> <span>CDL (any class)</span></label>
              <label class="cs-check"><input type="checkbox" name="cert" value="first_aid"/> <span>First Aid / CPR</span></label>
              <label class="cs-check"><input type="checkbox" name="cert" value="other_cert"/> <span>Other (specify below)</span></label>
            </div>
            <label class="cs-field cs-field-wide" style="margin-top:14px;">
              <span class="cs-field-k">Other certifications</span>
              <input type="text" name="other_certs" placeholder="DiGiCo, grandMA, BlackTrax, IATSE local, AHA-BLS, etc." />
            </label>
          </fieldset>

          <fieldset class="cs-block">
            <legend class="cs-legend">F &middot; Availability</legend>
            <div class="cs-grid">
              <label class="cs-field">
                <span class="cs-field-k">Status</span>
                <select name="status">
                  <option>Full-time available</option>
                  <option>Part-time / weekends</option>
                  <option>Evenings only</option>
                  <option>Project-by-project</option>
                  <option>Currently working &mdash; available in 60 days</option>
                </select>
              </label>
              <label class="cs-field">
                <span class="cs-field-k">Earliest start date</span>
                <input type="text" name="start_date" placeholder="ASAP or MM/DD" />
              </label>
              <label class="cs-field">
                <span class="cs-field-k">OK with overnight / load-out shifts?</span>
                <select name="overnight">
                  <option>Yes</option>
                  <option>Sometimes</option>
                  <option>No</option>
                </select>
              </label>
              <label class="cs-field">
                <span class="cs-field-k">Have your own gear / tools?</span>
                <select name="gear">
                  <option>Standard PPE only</option>
                  <option>PPE + basic hand tools</option>
                  <option>PPE + console / specialty gear</option>
                  <option>No gear yet</option>
                </select>
              </label>
            </div>
          </fieldset>

          <fieldset class="cs-block">
            <legend class="cs-legend">G &middot; Tell us about you</legend>
            <label class="cs-field cs-field-wide">
              <span class="cs-field-k">Anything in your background that translates</span>
              <textarea name="adjacent" rows="4" placeholder="Electrician, construction carpenter, home-theater installer, broadcast tech, IATSE local, AVL ministry, music school, service tech, etc. We hire on transferable skill."></textarea>
            </label>
            <label class="cs-field cs-field-wide" style="margin-top:14px;">
              <span class="cs-field-k">Why do you want to crew for us?</span>
              <textarea name="why" rows="3" placeholder="Optional but read every time. A few sentences in your own words."></textarea>
            </label>
            <label class="cs-field cs-field-wide" style="margin-top:14px;">
              <span class="cs-field-k">R&eacute;sum&eacute; (PDF, &lt; 5 MB)</span>
              <input type="file" name="resume" accept="application/pdf" class="apply-file" />
            </label>
            <label class="cs-field cs-field-wide" style="margin-top:14px;">
              <span class="cs-field-k">How did you hear about us?</span>
              <input type="text" name="referral" placeholder="Referral name / Instagram / Google / TikTok / Show Masters crew / etc." />
            </label>
          </fieldset>

          <div class="cs-foot">
            <div class="cs-sign">
              <span class="cs-stamp-mark" aria-hidden="true"></span>
              <span class="cs-sign-label">Routed to</span>
              <span class="cs-sign-line">SMPL &middot; Personnel Coordinator &middot; 5 business days</span>
            </div>
            <button type="submit" class="btn btn-primary btn-large cs-submit">Submit Application</button>
          </div>

          <div class="form-success" id="applySuccess" style="display:none; margin-top:32px;">
            <div class="form-success-icon" aria-hidden="true"><svg viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5l5 5L20 6"/></svg></div>
            <h3 style="margin-bottom:6px; font-family:'DM Serif Display',serif; font-size:1.6rem;">Application received.</h3>
            <p style="color:var(--text-2);">We review every submission and reply within five business days. If you do not hear back, email <a href="mailto:Orders@ShowMasters.com" class="gold">Orders@ShowMasters.com</a> with "Crew App &mdash; [Your Name]" in the subject.</p>
          </div>
        </form>"""
    s = s[:m2.start()] + NEW_FORM + s[m2.end():]
    print('Form replaced')
else:
    print('applyForm not found')

with open('careers.html','w',encoding='utf-8') as f:
    f.write(s)
print('careers.html written, %d lines' % s.count('\n'))

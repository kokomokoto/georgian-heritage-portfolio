"""
Emergency Site Restoration Guide
================================

ಠ_ಠ თუ საიტი ჩამტვრა, გაყევი ეს steps:

STEP 1: რევერტი უკან stable commit-მდე
git reset --hard 107f1f5
git push --force-with-lease

STEP 2: თუ ეგ არ იმუშავა, minimal app 
cp minimal_app.py app.py
git add -A
git commit -m "Emergency: minimal app for recovery"
git push

STEP 3: შემოწმება Render.com Dashboard
- შედი render.com/dashboard
- გადამოწმე logs
- შეცვალე environment variables თუ საჭიროა

STEP 4: ბოლო ალბათობა - ახალი service
- Deploy ახალი service Render.com-ზე
- დააკოპირე ყველა environment variable
- დააკონექტე GitHub repo

Working commits to rollback to:
================================
3b77677 Fix production deployment issues on Render.com  ✅ ეს მუშაობდა
107f1f5 bevrifoto  ✅ ეს მუშაობდა
10b8933 Implement multiple file upload ✅ ეს მუშაობდა
"""
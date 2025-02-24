# calendarsnack-cicd

CICD pipeline for calendarsnack solution

Development workflow outline (for backend):

  1. new features/bug fixes identified
  2. solution developed and tested
  3. version released to SAM App repo
      3a. Developer check-in:
      - git switch main
      - git pull origin main
      - git tag -am "Release vx.x.x" x.x.x
      - git push origin x.x.x
      3b. CodeBuild automation:
      - publish latest version of SAM apps (event management, shared lib, dashboard)
      - share published version with defined OU/account IDs
  4. internal and external packaged templates updated and tested
  5. announcement sent to stakeholders to use latest packaged template version (accessible from S3?)

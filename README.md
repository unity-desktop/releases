# releases

Build the unity-desktop apt repository from package uploads.

- Reads uploads from `ghcr.io/unity-desktop/oci-packages/<source>:<suite>`
- Publishes the repository to `ghcr.io/unity-desktop/ubuntu:<suite>`
- Lists each suite's packages in `suites/<suite>.yaml`
- Checks each upload before it goes in
- Signs the repository with aptly
- Runs from the `unity-desktop releases flow` workflow

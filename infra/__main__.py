import pulumi
import pulumi_gcp as gcp
import pulumi_docker as docker

# Configuration
config = pulumi.Config()
gcp_config = pulumi.Config("gcp")
project = gcp_config.require("project")
region = gcp_config.get("region") or "us-central1"

# Stack-specific configuration
service_cpu = config.get("service-cpu") or "1"
service_memory = config.get("service-memory") or "512Mi"
min_instances = config.get_int("min-instances") or 0
max_instances = config.get_int("max-instances") or 10

# ==============================================================================
# 1. ENABLE REQUIRED GCP APIS
# ==============================================================================

cloudrun_api = gcp.projects.Service(
    "cloudrun-api",
    service="run.googleapis.com",
    disable_on_destroy=False,
)

storage_api = gcp.projects.Service(
    "storage-api",
    service="storage.googleapis.com",
    disable_on_destroy=False,
)

firestore_api = gcp.projects.Service(
    "firestore-api",
    service="firestore.googleapis.com",
    disable_on_destroy=False,
)

artifactregistry_api = gcp.projects.Service(
    "artifactregistry-api",
    service="artifactregistry.googleapis.com",
    disable_on_destroy=False,
)

# ==============================================================================
# 2. ARTIFACT REGISTRY REPOSITORY (for Docker images)
# ==============================================================================

docker_repo = gcp.artifactregistry.Repository(
    "fognode-docker-repo",
    repository_id="fognode",
    location=region,
    format="DOCKER",
    description="Docker images for FogNode Audiobooks",
    opts=pulumi.ResourceOptions(depends_on=[artifactregistry_api]),
)

# ==============================================================================
# 3. CLOUD STORAGE BUCKET (for audio files)
# ==============================================================================

audio_bucket = gcp.storage.Bucket(
    "fognode-audiobooks-bucket",
    name=f"fognode-audiobooks-{project}",
    location=region.upper(),
    uniform_bucket_level_access=gcp.storage.BucketUniformBucketLevelAccessArgs(
        enabled=True,
    ),
    # Lifecycle rules for cost optimization
    lifecycle_rules=[
        gcp.storage.BucketLifecycleRuleArgs(
            action=gcp.storage.BucketLifecycleRuleActionArgs(type="Delete"),
            condition=gcp.storage.BucketLifecycleRuleConditionArgs(
                age=90,  # Delete files older than 90 days
            ),
        ),
    ],
    cors=[
        gcp.storage.BucketCorArgs(
            max_age_seconds=3600,
            methods=["GET", "HEAD"],
            origins=["*"],
            response_headers=["Content-Type"],
        ),
    ],
    opts=pulumi.ResourceOptions(depends_on=[storage_api]),
)

# ==============================================================================
# 4. FIRESTORE DATABASE (for job metadata)
# ==============================================================================

firestore_db = gcp.firestore.Database(
    "fognode-firestore-db",
    name="(default)",
    location_id=region,
    type="FIRESTORE_NATIVE",
    opts=pulumi.ResourceOptions(depends_on=[firestore_api]),
)

# ==============================================================================
# 5. SERVICE ACCOUNT & IAM PERMISSIONS
# ==============================================================================

service_account = gcp.serviceaccount.Account(
    "fognode-service-account",
    account_id="fognode-api",
    display_name="FogNode API Service Account",
    description="Service account for FogNode Cloud Run service",
)

# Grant Storage Object Admin role (for bucket operations)
storage_iam_binding = gcp.storage.BucketIAMBinding(
    "fognode-bucket-iam",
    bucket=audio_bucket.name,
    role="roles/storage.objectAdmin",
    members=[service_account.email.apply(lambda email: f"serviceAccount:{email}")],
)

# Grant Firestore User role (for database operations)
firestore_iam_binding = gcp.projects.IAMMember(
    "fognode-firestore-iam",
    project=project,
    role="roles/datastore.user",
    member=service_account.email.apply(lambda email: f"serviceAccount:{email}"),
)

# ==============================================================================
# 6. BUILD & PUSH DOCKER IMAGE
# ==============================================================================

# Docker image name in Artifact Registry
image_name = pulumi.Output.concat(
    region,
    "-docker.pkg.dev/",
    project,
    "/",
    docker_repo.repository_id,
    "/fognode-api:latest",
)

# Build and push image
# Note: This requires Docker to be installed and authenticated with gcloud
app_image = docker.Image(
    "fognode-app-image",
    image_name=image_name,
    build=docker.DockerBuildArgs(
        context="../",  # Build from project root
        dockerfile="../Dockerfile",
        platform="linux/amd64",
    ),
    registry=docker.RegistryArgs(
        # Use gcloud credential helper
        server=pulumi.Output.concat(region, "-docker.pkg.dev"),
    ),
    opts=pulumi.ResourceOptions(depends_on=[docker_repo]),
)

# ==============================================================================
# 7. CLOUD RUN SERVICE
# ==============================================================================

cloud_run_service = gcp.cloudrunv2.Service(
    "fognode-api-service",
    name="fognode-api",
    location=region,
    template=gcp.cloudrunv2.ServiceTemplateArgs(
        service_account=service_account.email,
        containers=[
            gcp.cloudrunv2.ServiceTemplateContainerArgs(
                image=app_image.image_name,
                ports=[
                    gcp.cloudrunv2.ServiceTemplateContainerPortArgs(
                        container_port=8000,
                    ),
                ],
                resources=gcp.cloudrunv2.ServiceTemplateContainerResourcesArgs(
                    limits={
                        "cpu": service_cpu,
                        "memory": service_memory,
                    },
                ),
                envs=[
                    gcp.cloudrunv2.ServiceTemplateContainerEnvArgs(
                        name="GCP_PROJECT_ID",
                        value=project,
                    ),
                    gcp.cloudrunv2.ServiceTemplateContainerEnvArgs(
                        name="BUCKET_NAME",
                        value=audio_bucket.name,
                    ),
                    gcp.cloudrunv2.ServiceTemplateContainerEnvArgs(
                        name="ENV_MODE",
                        value="production",
                    ),
                ],
            ),
        ],
        scaling=gcp.cloudrunv2.ServiceTemplateScalingArgs(
            min_instance_count=min_instances,
            max_instance_count=max_instances,
        ),
    ),
    opts=pulumi.ResourceOptions(
        depends_on=[
            cloudrun_api,
            service_account,
            storage_iam_binding,
            firestore_iam_binding,
        ]
    ),
)

# Make Cloud Run service publicly accessible
cloud_run_iam = gcp.cloudrunv2.ServiceIamBinding(
    "fognode-api-public-access",
    name=cloud_run_service.name,
    location=region,
    role="roles/run.invoker",
    members=["allUsers"],  # Make it public
)

# ==============================================================================
# OUTPUTS
# ==============================================================================

pulumi.export("service_url", cloud_run_service.uri)
pulumi.export("bucket_name", audio_bucket.name)
pulumi.export("bucket_url", audio_bucket.url)
pulumi.export("docker_repo_url", docker_repo.name)
pulumi.export("service_account_email", service_account.email)
pulumi.export("project_id", project)
pulumi.export("region", region)

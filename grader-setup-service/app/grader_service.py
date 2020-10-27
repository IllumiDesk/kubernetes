import os
from secrets import token_hex

from kubernetes import client
from kubernetes import config
from kubernetes.config import ConfigException


DEPLOYMENT_NAME_TEMPLATE = 'grader-deployment-{0}'
NAMESPACE = 'default'
KUBE_CONFIG_FILE = os.environ.get('KUBE_CONFIG_FILE')


class GraderServiceLauncher:
    def __init__(self, course_id: str):
        # try to load the cluster credentials
        try:
            # Configs can be set in Configuration class directly or using helper utility
            config.load_incluster_config()
        except ConfigException:
            config.load_kube_config(config_file=KUBE_CONFIG_FILE)
        # Uncomment the following lines to enable debug logging
        # c = client.Configuration()
        # c.debug = True
        # apps_v1 = client.AppsV1Api(api_client=client.ApiClient(configuration=c))
        self.apps_v1 = client.AppsV1Api()
        self.course_id = course_id
        self.grader_name = f'grader-{self.course_id}'
        self.deployment_name = DEPLOYMENT_NAME_TEMPLATE.format(self.grader_name)

    def grader_deployment_exists(self) -> bool:
        """
        Check if there is a deployment for the grader service name        
        """
        # Filter deployments by the current namespace and a specific name (metadata collection)
        deployment_list = self.apps_v1.list_namespaced_deployment(namespace=NAMESPACE, field_selector=f'metadata.name={self.deployment_name}')
        if deployment_list and deployment_list.items:            
            return True
        
        return False

    def create_grader_deployment(self):
        # Create grader deployement
        deployment = self._create_deployment_object()
        api_response = self.apps_v1.create_namespaced_deployment(body=deployment, namespace=NAMESPACE)
        print("Deployment created. status='%s'" % str(api_response.status))

    def _create_deployment_object(self):
        grader_token = token_hex(32)
        # Configureate Pod template container
        container = client.V1Container(
            name='grader-notebook',
            image='illumidesk/grader-notebook:latest',
            command=['start-notebook.sh', f'--group=formgrade-{self.course_id}'],
            ports=[client.V1ContainerPort(container_port=8888)],
            resources=client.V1ResourceRequirements(
                requests={"cpu": "100m", "memory": "200Mi"}, limits={"cpu": "500m", "memory": "500Mi"}
            ),
            env=[
                client.V1EnvVar(name='JUPYTERHUB_SERVICE_NAME', value=self.course_id),
                client.V1EnvVar(name='JUPYTERHUB_API_TOKEN', value=grader_token),
                client.V1EnvVar(name='JUPYTERHUB_API_URL', value='http://hub:8081/hub/api'),
                client.V1EnvVar(name='JUPYTERHUB_BASE_URL', value='/'),
                client.V1EnvVar(name='JUPYTERHUB_SERVICE_PREFIX', value=f'/services/{self.course_id}'),
                client.V1EnvVar(name='JUPYTERHUB_USER', value=self.grader_name),
                client.V1EnvVar(name='NB_GRADER_UID', value='10001'),
                client.V1EnvVar(name='NB_GID', value='100'),
                client.V1EnvVar(name='NB_USER', value=self.grader_name),
                # todo: validate if this env var is still required
                client.V1EnvVar(name='USER_ROLE', value='Grader'),
            ]
        )
        # Create and configurate a spec section
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={'app': f'grader-notebook-{self.course_id}'}),
            spec=client.V1PodSpec(containers=[container]),
        )
        # Create the specification of deployment
        spec = client.V1DeploymentSpec(
            replicas=1, template=template, selector={'matchLabels': {'app': f'grader-notebook-{self.course_id}'}}
        )
        # Instantiate the deployment object
        deployment = client.V1Deployment(
            api_version="apps/v1", kind="Deployment", metadata=client.V1ObjectMeta(name=self.deployment_name), spec=spec
        )

        return deployment


class KubernetesApiClient:
    def __init__(self):
        # load
        try:
            config.load_incluster_config()
        except ConfigException:
            config.load_kube_config()

        self.configuration = client.Configuration()

    def create_job_object(self, job_name, container_image, args):
        volume_name = ""  # volume inside of which you put your service account
        google_app_credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        volume_mount = client.V1VolumeMount(
            mount_path='/'.join(google_app_credentials_path.split('/')[:-1]), name=volume_name
        )

        env = client.V1EnvVar(name='GOOGLE_APPLICATION_CREDENTIALS', value=google_app_credentials_path)
        container = client.V1Container(
            name=job_name,
            image=container_image,
            args=args,
            volume_mounts=[volume_mount],
            env=[env],
            image_pull_policy="Always",
        )

        volume = client.V1Volume(
            name=volume_name,
            secret=client.V1SecretVolumeSource(secret_name='<secret-where-you-put-the-service-account>'),
        )

        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"app": "sample"}),
            spec=client.V1PodSpec(restart_policy="Never", containers=[container], volumes=[volume]),
        )

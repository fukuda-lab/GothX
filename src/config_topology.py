class ConfigTopo:
    def __init__(self,
                 routers_to_configure: list[str],
                 CREATE_MIRAI_NODES: bool,
                 MUSEUM: bool,
                 LABS: bool,
                 AUTO_CONFIGURE_ROUTERS: bool,
                 STEEL: bool,
                 NEIGHBORHOOD: bool,
                 SINETSTREAM: bool,
                 MQTT_TLS_BROKER_DEVICES: bool,
                 MQTTSET_ATTACKS: bool,
                 nb_domotic_clusters: int,
                 domotic_devices_per_cluster: int,
                 nb_cooler_plain_clusters: int,
                 cooler_plain_devices_per_cluster: int,
                 nb_pred_plain_clusters: int,
                 pred_plain_devices_per_cluster: int,
                 nb_cooler_tls_devices: int,
                 nb_pred_tls_clusters: int,
                 pred_tls_devices_per_cluster: int,
                 ):
        for nb_per_cluster in (domotic_devices_per_cluster,
                               cooler_plain_devices_per_cluster,
                               pred_tls_devices_per_cluster,
                               pred_plain_devices_per_cluster,
                               nb_cooler_tls_devices):
            if nb_per_cluster > 15:
                raise ValueError(f"Cannot have {nb_per_cluster=}. It must be <= 15")

        self.routers_to_configure = routers_to_configure

        self.CREATE_MIRAI_NODES = CREATE_MIRAI_NODES
        self.MUSEUM = MUSEUM
        self.LABS = LABS

        self.AUTO_CONFIGURE_ROUTERS = AUTO_CONFIGURE_ROUTERS
        self.STEEL = STEEL
        self.NEIGHBORHOOD = NEIGHBORHOOD
        self.SINETSTREAM = SINETSTREAM
        self.MQTT_TLS_BROKER_DEVICES = MQTT_TLS_BROKER_DEVICES
        self.MQTTSET_ATTACKS = MQTTSET_ATTACKS

        # in NEIGHBORHOOD
        self.nb_domotic_clusters = nb_domotic_clusters
        self.domotic_devices_per_cluster = domotic_devices_per_cluster
        # in STEEL plain (no tls)
        self.nb_cooler_plain_clusters = nb_cooler_plain_clusters
        self.cooler_plain_devices_per_cluster = cooler_plain_devices_per_cluster
        self.nb_pred_plain_clusters = nb_pred_plain_clusters
        self.pred_plain_devices_per_cluster = pred_plain_devices_per_cluster
        # in STEEL tls
        self.nb_cooler_tls_devices = nb_cooler_tls_devices
        self.nb_pred_tls_clusters = nb_pred_tls_clusters
        self.pred_tls_devices_per_cluster = pred_tls_devices_per_cluster

    def __str__(self):
        nb_sensors = self.nb_domotic_clusters * self.domotic_devices_per_cluster + \
                     self.nb_cooler_plain_clusters * self.cooler_plain_devices_per_cluster + \
                     self.nb_pred_plain_clusters * self.pred_plain_devices_per_cluster + \
                     self.nb_cooler_tls_devices + \
                     self.nb_pred_tls_clusters * self.pred_tls_devices_per_cluster

        return f"{nb_sensors} sensors simulated"

config_topology_propositions: dict[str, ConfigTopo] = {
    "mqttset": ConfigTopo(
        routers_to_configure=[f"VyOS1.3.0-{i}" for i in (1, 2, 3, 5, 10)],
        AUTO_CONFIGURE_ROUTERS=True,
        CREATE_MIRAI_NODES=False,
        MUSEUM=False,
        LABS=False,
        STEEL=True,
        NEIGHBORHOOD=True,
        SINETSTREAM=False,
        MQTT_TLS_BROKER_DEVICES=False,
        MQTTSET_ATTACKS=True,
        nb_domotic_clusters=1,
        domotic_devices_per_cluster=10,
        nb_cooler_plain_clusters=0,
        cooler_plain_devices_per_cluster=0,
        nb_pred_plain_clusters=0,
        pred_plain_devices_per_cluster=0,
        nb_cooler_tls_devices=0,
        nb_pred_tls_clusters=0,
        pred_tls_devices_per_cluster=0,
    ),
    "sinetstream_small": ConfigTopo(
        routers_to_configure=[f"VyOS1.3.0-{i}" for i in (1, 2, 5, 6)],
        AUTO_CONFIGURE_ROUTERS=True,
        CREATE_MIRAI_NODES=False,
        MUSEUM=False,
        LABS=False,
        STEEL=True,
        NEIGHBORHOOD=True,
        SINETSTREAM=True,
        MQTT_TLS_BROKER_DEVICES=True,
        MQTTSET_ATTACKS=False,
        nb_domotic_clusters=1,
        domotic_devices_per_cluster=3,
        nb_cooler_plain_clusters=1,
        cooler_plain_devices_per_cluster=3,
        nb_pred_plain_clusters=1,
        pred_plain_devices_per_cluster=4,
        nb_cooler_tls_devices=2,
        nb_pred_tls_clusters=1,
        pred_tls_devices_per_cluster=2,
    ),
    "sinetstream_big": ConfigTopo(
        routers_to_configure=[f"VyOS1.3.0-{i}" for i in (1, 2, 5, 6)],
        AUTO_CONFIGURE_ROUTERS=True,
        CREATE_MIRAI_NODES=False,
        MUSEUM=False,
        LABS=False,
        STEEL=True,
        NEIGHBORHOOD=True,
        SINETSTREAM=True,
        MQTT_TLS_BROKER_DEVICES=True,
        MQTTSET_ATTACKS=False,
        nb_domotic_clusters=2,
        domotic_devices_per_cluster=15,
        nb_cooler_plain_clusters=1,
        cooler_plain_devices_per_cluster=15,
        nb_pred_plain_clusters=2,
        pred_plain_devices_per_cluster=15,
        nb_cooler_tls_devices=10,
        nb_pred_tls_clusters=2,
        pred_tls_devices_per_cluster=15,
    ),
    "sinetstream_max": ConfigTopo(
        routers_to_configure=[f"VyOS1.3.0-{i}" for i in (1, 2, 5, 6)],
        AUTO_CONFIGURE_ROUTERS=True,
        CREATE_MIRAI_NODES=False,
        MUSEUM=False,
        LABS=False,
        STEEL=True,
        NEIGHBORHOOD=True,
        SINETSTREAM=True,
        MQTT_TLS_BROKER_DEVICES=True,
        MQTTSET_ATTACKS=False,
        nb_domotic_clusters=15,
        domotic_devices_per_cluster=15,
        nb_cooler_plain_clusters=3,
        cooler_plain_devices_per_cluster=15,
        nb_pred_plain_clusters=4,
        pred_plain_devices_per_cluster=15,
        nb_cooler_tls_devices=15,
        nb_pred_tls_clusters=7,
        pred_tls_devices_per_cluster=15,
    ),
}

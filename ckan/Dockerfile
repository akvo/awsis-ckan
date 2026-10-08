FROM ckan/ckan-base:2.11.6


# Install any extensions needed by your CKAN instance
# See Dockerfile.dev for more details and examples


USER root

ARG QSV_VERSION=13.0.0
ARG DPP_VERSION=3.0.0


RUN apt-get install -y \
    python3-dev \
    python3-lxml \
    libgeos-dev \
    libmagic1 \
    unzip \
    uchardet \
    file \
    cron

# musl build: the glibc build needs GLIBC 2.39, the bookworm base has 2.36
RUN wget -q https://github.com/dathere/qsv/releases/download/${QSV_VERSION}/qsv-${QSV_VERSION}-x86_64-unknown-linux-musl.zip -O /tmp/qsv.zip && \
    unzip -q /tmp/qsv.zip -d /tmp/qsv && \
    mv /tmp/qsv/qsv* /usr/local/bin/ && \
    rm -rf /tmp/qsv /tmp/qsv.zip


RUN pip3 install -e 'git+https://github.com/ckan/ckanext-basiccharts.git@dfe2c4f5859c29f72960ed416f7f2bd77e3c3090#egg=ckanext-basiccharts'
RUN pip3 install -e 'git+https://github.com/keitaroinc/ckanext-visualize.git@eb53fd00b6a99efd9d8924543ec3bb22774ec083#egg=ckanext-visualize'
RUN pip3 install geojson==3.3.0 shapely==2.1.2 ckanext-pdfview==0.0.6 ckanext-contact==2.4.4
RUN pip3 install -e 'git+https://github.com/ckan/ckanext-geoview.git@v0.2.2#egg=ckanext-geoview'
RUN pip3 install -e 'git+https://github.com/ckan/ckanext-spatial.git@v2.3.2#egg=ckanext-spatial'
RUN pip3 install -e 'git+https://github.com/ckan/ckanext-hierarchy.git@53c1ee74805d79aef7c9c01cc513eb881cb8928f#egg=ckanext-hierarchy' && pip3 install -r ${APP_DIR}/src/ckanext-hierarchy/requirements.txt
RUN pip3 install -e 'git+https://github.com/ckan/ckanext-mapviews.git@caf1d0f6ab4168f3ac10a75881fa537144b01d34#egg=ckanext-mapviews'
# DP+ pins shapely==2.1.0; ckanext-spatial needs ~=2.1.2 (patch release, compatible with both)
RUN pip3 install -e "git+https://github.com/dathere/datapusher-plus.git@${DPP_VERSION}#egg=datapusher-plus" && pip3 install -r ${APP_DIR}/src/datapusher-plus/requirements.txt && \
    pip3 install "shapely==2.1.2"
# DP+ reads qsv_bin at import time, before its config defaults apply
RUN ckan config-tool ${CKAN_INI} "ckanext.datapusher_plus.qsv_bin=/usr/local/bin/qsvdp"

# Copy custom initialization scripts
COPY docker-entrypoint.d/* /docker-entrypoint.d/

# Copy cron file
COPY cron.txt ${APP_DIR}/

# Import the crontab
RUN crontab ${APP_DIR}/cron.txt

# Apply any patches needed to CKAN core or any of the built extensions (not the
# runtime mounted ones)
COPY patches ${APP_DIR}/patches

RUN for d in $APP_DIR/patches/*; do \
        if [ -d $d ]; then \
            for f in `ls $d/*.patch | sort -g`; do \
                cd $SRC_DIR/`basename "$d"` && echo "$0: Applying patch $f to $SRC_DIR/`basename $d`"; patch -p1 < "$f" ; \
            done ; \
        fi ; \
    done

COPY setup/start_ckan.sh.override.2.11 ${APP_DIR}/start_ckan.sh
RUN chown ckan-sys:ckan-sys ${APP_DIR}/start_ckan.sh
RUN chmod 755 ${APP_DIR}/start_ckan.sh
from django.conf.urls import patterns, include, url
from django.contrib import admin
from appl_wisdom_admin_interface.wai_view import wai_login, wai_logout, wai_mngvalmas, createvalmas, insvalmas, viewdat, editvalmas, delmasdat, wai_mngprojob, wai_header, wai_mngprocmoni, wai_mngcliven, get_name, viewvalmasdet, upprojobs, wai_mngadmuser, wai_crtuser, wai_upprojdets, wai_insprojdet, wai_usrpermission, wai_insjobdet, wai_usrupdperms, wai_forgot, wai_chgpwd, wai_procsjobs, wai_valmasidgen, wai_insclidet, wai_clivendet, wai_insvendet, wai_ext_projid_name, wai_mngpgvalmas, wai_ext_clientid_name, wai_ext_venueid_name, wai_updprojidnaext, wai_updextjobidna, wai_extjobidna, wai_extupdcliidna, wai_extupdvenidna, wai_extusridna, wai_mngblacal, wai_mnglevevtcal, wai_mnglivevt, wai_mngcon, wai_mngsplact, wai_loadvenudet, wai_mngcreblacal, wai_mngsplcrtrol, submit_role, wai_mngsplcrtusr, submit_user, wai_sessionvenuid

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'wisdom_val_det.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^$', wai_login),    

    url(r'^admin/', include(admin.site.urls)),

    url(r'^wai_login/$', wai_login),
    url(r'^wai_logout/$', wai_logout),
    url(r'^wai_forgot/$', wai_forgot),

    url(r'^wai_mngvalmas/$', wai_mngvalmas),
    url(r'^createvalmas/$', createvalmas),
    url(r'^insvalmas/$', insvalmas),
    url(r'^viewdat/$', viewdat),
    url(r'^editvalmas/$', editvalmas),    
    url(r'^delmasdat/$', delmasdat),
    url(r'^wai_valmasidgen/$', wai_valmasidgen),
    url(r'^wai_mngpgvalmas/$', wai_mngpgvalmas),

    url(r'^wai_mngprojob/$', wai_mngprojob),
    url(r'^wai_insprojdet/$', wai_insprojdet),
    url(r'^wai_upprojdets/$', wai_upprojdets),
    url(r'^upprojobs/$', upprojobs),
    url(r'^wai_insjobdet/$', wai_insjobdet),
    url(r'^wai_ext_projid_name/$', wai_ext_projid_name),
    url(r'^wai_updprojidnaext/$', wai_updprojidnaext),
    url(r'^wai_updextjobidna/$', wai_updextjobidna),
    url(r'^wai_extjobidna/$', wai_extjobidna),

    url(r'^wai_mngprocmoni/$', wai_mngprocmoni), 
    url(r'^wai_procsjobs/$', wai_procsjobs),

    url(r'^wai_mngcliven/$', wai_mngcliven),
    url(r'^wai_ext_clientid_name/$', wai_ext_clientid_name),
    url(r'^wai_insclidet/$', wai_insclidet),
    url(r'^wai_clivendet/$', wai_clivendet),
    url(r'^wai_ext_venueid_name/$', wai_ext_venueid_name),
    url(r'^wai_insvendet/$', wai_insvendet),
    url(r'^wai_extupdcliidna/$', wai_extupdcliidna),
    url(r'^wai_extupdvenidna/$', wai_extupdvenidna),
    url(R'^wai_sessionvenuid/$', wai_sessionvenuid),

    url(r'^wai_mngadmuser/$', wai_mngadmuser),
    url(r'^wai_crtuser/$', wai_crtuser),
    url(r'^wai_usrpermission/$', wai_usrpermission),
    url(r'^wai_usrupdperms/$', wai_usrupdperms),
    url(r'^wai_chgpwd/$', wai_chgpwd),
    url(r'^wai_extusridna/$', wai_extusridna),

    url(r'^wai_mngblacal/$', wai_mngblacal),
    url(r'^wai_mngcreblacal/$', wai_mngcreblacal),
    url(r'^wai_mnglevevtcal/$',wai_mnglevevtcal),
    url(r'^wai_mnglivevt/$',wai_mnglivevt),

    url(r'^wai_mngcon/$', wai_mngcon),

    url(r'^wai_mngsplact/$', wai_mngsplact),
    url(r'^wai_mngsplcrtrol/$', wai_mngsplcrtrol), 
    url(r'^submit_role/$', submit_role),
    url(r'^wai_mngsplcrtusr/$', wai_mngsplcrtusr),
    url(r'^submit_user/$', submit_user),

    url(r'^wai_loadvenudet/$', wai_loadvenudet),

    url(r'^wai_header/$', wai_header),

    url(r'^ajaxexample$', 'appl_wisdom_admin_interface.wai_view.main'),
    url(r'^ajaxexample_json$', 'appl_wisdom_admin_interface.wai_view.ajax'),

#Extras
    url(r'^get_name/$', get_name),
    url(r'^viewvalmasdet/$', viewvalmasdet)
#    url(r'^valmaster/$',valmaster)
)

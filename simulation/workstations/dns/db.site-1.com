
$TTL       604800
@       IN      SOA     site-1.com. admin.site-1.com. (
                                 3       ;     Serial
                            604800       ;     Refresh
                             86400       ;     Retry
                           2419200       ;     Expire
                            604800   )   ;     Negative Cache TTL
;
; name servers - NS records
@        IN      NS      site-1.com.
site-1.com.   IN      A       10.122.0.20
www.site-1.com.   IN      CNAME       site-1.com.

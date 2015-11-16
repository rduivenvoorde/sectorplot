-- base64, hex, escape
select length(zoneradii), encode(zoneradii, 'hex'), zoneradii from npp limit 1
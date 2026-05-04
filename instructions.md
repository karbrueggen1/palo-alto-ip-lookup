We want to build an ip lookup tool for palo alto EDL.

Initial Information:
More information about the EDL service can be found here: https://docs.paloaltonetworks.com/resources/edl-hosting-service
The EDL comes as URL EDL or IP EDL.
With IP EDL, a list ob subnets is provided.
this is one of the palo alto ipv4 edl lists: https://saasedl.paloaltonetworks.com/feeds/azure/public/actiongroup/ipv4
there are many more lists and all of them must be queried. the main page where all the other edl are linked is https://docs.paloaltonetworks.com/resources/edl-hosting-service

Goal:
I want a script where i can input an ipv4 address or ipv4 network and the script checks, if the ip is in one of the palo alto edl lists.
ipv4 format can be 52.123.224.73 for a single address or 52.123.224.0/24 for a network.
if ip adress is found in one of the subnets, the script should print all EDLs with their Name and URL, where the ip address is included.
Only focus on Europe/Germany/WorldWide lists

More Information:
the ip edl contains a list of subnets. so the script must calculate, if the provided ip address is in one of the subnets.
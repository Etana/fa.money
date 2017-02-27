fa.money
========

small google app engine python app for transfering points between forum members

an outdated french tutorial to set it up is accessible [here](http://forum.forumactif.com/t345724-hide-argent-virtuel#2956566)

## routes

* /fa_money/forumotion.forum.domain/admin => to set up a forum's admin login and password
* /fa_money/forumotion.forum.domain/history/number => to see the history of point transfering of a member identified by number ( 1-... )
* /fa_money/forumotion.forum.domain/ => url used by script on the forum, for transfering poing

remplace `forumotion.forum.domain` by your domain

## setup

* clone this repo or [download zip](http://i.imgur.com/jt4Bb9X.png) and unzip
* follow instructions to install and setup cloud tools on https://cloud.google.com/sdk/docs/
* you should have an account with a google developer project and gcloud set to this project
* go to the fa.money sources in directory `money` and do this command or equivalent `gcloud app deploy app.yaml index.yaml`
* go to the admin interface `http://<your_dev_project_name>.appspot.com/fa_money/<your.forum.domain.name>/admin` and configure an the username and password of a forum administrator
* copy the script and add it on the target forum on all pages ([`Index`](http://votre-forum.appspot.com/#/admin/,&part=modules,&sub=html) > [`Panneau d'administration`](http://votre-forum.appspot.com/admin/#&part=modules,&sub=html) > [`Modules`](http://votre-forum.appspot.com/admin/?part=modules#&sub=html) > [`HTML & JAVASCRIPT | Gestion des pages HTML`](http://votre-forum.appspot.com/admin/?part=modules&sub=html))

The admin interface of the application should be available at `http://<your_dev_project_name>.appspot.com/fa_money/<your.forum.domain.name>/admin` to the project owner and users with App Engine Admin role in [IAM](https://console.cloud.google.com/iam-admin/iam/iam-zero) for the project.
